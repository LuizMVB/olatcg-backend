import os, tempfile, subprocess
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.constants import TAX_ID_FILE, NODES_FILE, NAMES_FILE
from core.models import Taxonomy, Alignment, BiologicalSequence, BiologicalSequenceTypeChoices, Analysis, BlastnInput, \
    BlastnOutput
from core.serializers import AnalysisHomologyRequestSerializer


class AnalysisHomologyView(APIView):
    def run_blast(self, query_file_path, db, evalue, gapopen, gapextend, penalty):
        """Runs the BLASTn command with the specified parameters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.out') as output_file:
            output_file_path = output_file.name

        blastn_command = [
            'blastn',
            '-query', query_file_path,
            '-db', db,
            '-evalue', str(evalue),
            '-gapopen', str(gapopen),
            '-gapextend', str(gapextend),
            '-penalty', str(penalty),
            '-outfmt', '11',
            '-out', output_file_path
        ]

        result = subprocess.run(blastn_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, blastn_command, output=result.stdout,
                                                stderr=result.stderr)

        return output_file_path

    def format_blast_output(self, blast_output_path):
        """Formats the BLAST output using the blast_formatter command."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as formatted_output_file:
            formatted_output_path = formatted_output_file.name

        blast_formatter_command = [
            'blast_formatter',
            '-archive', blast_output_path,
            '-outfmt', '6 qseqid sseqid pident length qlen slen score evalue qseq sseq',
            '-out', formatted_output_path
        ]

        formatter_result = subprocess.run(blast_formatter_command, capture_output=True, text=True)

        if formatter_result.returncode != 0:
            raise subprocess.CalledProcessError(formatter_result.returncode, blast_formatter_command,
                                                output=formatter_result.stdout, stderr=formatter_result.stderr)

        return formatted_output_path

    def load_taxid_map(self, taxid_map_file):
        taxid_map = {}
        with open(taxid_map_file) as f:
            for line in f:
                seq_id, tax_id = line.strip().split()
                taxid_map[seq_id] = tax_id
        return taxid_map

    def load_nodes(self, nodes_file):
        nodes = {}
        with open(nodes_file) as f:
            for line in f:
                parts = line.strip().split('|')
                tax_id = parts[0].strip()
                parent_id = parts[1].strip()
                rank = parts[2].strip()
                nodes[tax_id] = {'parent': parent_id, 'rank': rank}
        return nodes

    def load_names(self, names_file):
        names = {}
        with open(names_file) as f:
            for line in f:
                parts = line.strip().split('|')
                tax_id = parts[0].strip()
                name = parts[1].strip()
                name_class = parts[3].strip()
                if name_class == "scientific name":
                    names[tax_id] = name
        return names

    def get_lineage(self, tax_id, nodes, names):
        lineage = []
        while tax_id != '1':  # Continue while tax_id is not root
            name = names.get(tax_id, 'unknown')
            lineage.append(name)
            if tax_id not in nodes:
                break  # Stop if tax_id not found in nodes
            parent_id = nodes[tax_id]['parent']
            tax_id = parent_id

        if tax_id == '1':
            lineage.append('root')

        return '; '.join(lineage[::-1])

    def parse_blast_results(self, analysis, blast_results, query_titles, taxid_map, nodes, names):
        """Parses the BLAST results into a structured format."""
        parsed_results = {}
        taxonomies = []
        alignments = []
        biological_sequences = []
        for line in blast_results:
            cols = line.strip().split("\t")
            query_id = cols[0]
            subject_id = cols[1].split('|')[1]  # Adjusted to match taxid_map key format
            tax_id = taxid_map.get(subject_id, "unknown")
            lineage = self.get_lineage(tax_id, nodes, names) if tax_id != "unknown" else "unknown"
            query_seq = cols[8]
            subject_seq = cols[9]

            hit = {
                'subject_id': cols[1],
                'tax_id': tax_id,
                'lineage': lineage,
                'percent_identity': float(cols[2]),
                'alignment_length': int(cols[3]),
                'query_length': int(cols[4]),
                'subject_length': int(cols[5]),
                'score': float(cols[6]),
                'evalue': float(cols[7]),
                'query_sequence': query_seq,
                'subject_sequence': subject_seq,
            }

            if query_id not in parsed_results:
                parsed_results[query_id] = {
                    'query_id': query_id,
                    'query_title': query_titles.get(query_id, ''),  # Get query title from the dictionary
                    'query_len': hit['query_length'],
                    'hits': []
                }

            parsed_results[query_id]['hits'].append(hit)

            taxonomy = Taxonomy(
                analysis=analysis,
                external_tax_id=tax_id,
                title=f'{subject_id}|{tax_id}',
                lineage=lineage
            )

            taxonomies.append(taxonomy)

            alignment = Alignment(
                taxonomy=taxonomy,
                analysis=analysis
            )

            alignments.append(alignment)

            biological_sequences.append(BiologicalSequence(
                alignment=alignment,
                bases=query_seq,
                external_sequence_id=query_id,
                type=BiologicalSequenceTypeChoices.GAPPED_DNA
            ))

            biological_sequences.append(BiologicalSequence(
                alignment=alignment,
                bases=subject_seq,
                external_sequence_id=subject_id,
                type=BiologicalSequenceTypeChoices.GAPPED_DNA
            ))

        Taxonomy.objects.bulk_create(taxonomies)
        Alignment.objects.bulk_create(alignments)
        BiologicalSequence.objects.bulk_create(biological_sequences)

        return list(parsed_results.values())

    def perform_homology_analysis(self, data, analysis, all_results, query_titles, query_file_path, taxid_map, nodes,
                                  names):
        blast_outfmt11_path = self.run_blast(query_file_path,
                                             data['database'],
                                             data['evalue'],
                                             data['gap_open'],
                                             data['gap_extend'],
                                             data['penalty'])

        blast_outfmt6_path = self.format_blast_output(blast_outfmt11_path)

        with open(blast_outfmt6_path, 'r') as f:
            blast_results = f.readlines()

        parsed_results = self.parse_blast_results(analysis, blast_results, query_titles, taxid_map, nodes, names)

        if len(parsed_results) > 0:
            all_results.extend(parsed_results)

        return blast_outfmt11_path, blast_outfmt6_path

    def create_query_file(self, data, query_titles):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as query_file:
            for sequence in data['biological_sequences']:
                title = sequence.get('title', '')
                bases = sequence.get('bases')
                if bases:
                    query_id = f"query_{len(query_titles) + 1}"
                    query_titles[query_id] = title
                    query_file.write(f">{query_id} {title}\n{bases}\n".encode())
            query_file_path = query_file.name

        if os.path.getsize(query_file_path) == 0:
            return Response({"error": "No valid sequences provided."}, status=status.HTTP_400_BAD_REQUEST)

        return query_file_path

    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        """Handles the POST request to run the homology analysis."""

        request_serializer = AnalysisHomologyRequestSerializer(
            data=request.data,
            context={'analysis_id': analysis_id})

        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status.HTTP_400_BAD_REQUEST)

        analysis = Analysis.objects.get(id=analysis_id)
        data = request_serializer.validated_data

        all_results = []
        query_titles = {}

        query_file_path = self.create_query_file(data, query_titles)

        with open(query_file_path, 'rb') as query_file:
            blastn_input = BlastnInput.objects.create(
                analysis=analysis,
                database=data['database'],
                evalue=data['evalue'],
                gap_open=data['gap_open'],
                gap_extend=data['gap_extend'],
                penalty=data['penalty'],
                input_file=query_file.read()
            )
            blastn_input.save()

        taxid_map = self.load_taxid_map(TAX_ID_FILE)
        nodes = self.load_nodes(NODES_FILE)
        names = self.load_names(NAMES_FILE)

        blast_outfmt11_path, blast_outfmt6_path = self.perform_homology_analysis(
            data, analysis, all_results, query_titles, query_file_path, taxid_map, nodes, names)

        with open(blast_outfmt11_path, 'rb') as blast_output_file:
            blastn_output = BlastnOutput.objects.create(
                input=blastn_input,
                output_file=blast_output_file.read()
            )
            blastn_output.save()

        os.remove(query_file_path)
        os.remove(blast_outfmt11_path)
        os.remove(blast_outfmt6_path)

        return Response(all_results, status=status.HTTP_200_OK)