import tempfile, subprocess
from Bio.Blast import NCBIXML
from django.db import transaction
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Analysis, AnalysisTypeChoices, AnalysisStatusChoices, MuscleInput, MuscleOutput, FastTreeInput, \
    FastTreeOutput, BlastnInput, BlastnOutput
from core.serializers import AnalysisTreeSerializer


class AnalysisTreeView(APIView):

    def format_blast_output_to_xml(self, blast_output_binary):
        """Formats the BLAST output to XML (outfmt 5) using the blast_formatter command."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.asn') as temp_blast_output:
            temp_blast_output.write(blast_output_binary)
            temp_blast_output_path = temp_blast_output.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as formatted_output_file:
            formatted_output_path = formatted_output_file.name

        blast_formatter_command = [
            'blast_formatter',
            '-archive', temp_blast_output_path,
            '-outfmt', '5',  # XML format
            '-out', formatted_output_file.name
        ]

        formatter_result = subprocess.run(blast_formatter_command, text=True)

        if formatter_result.returncode != 0:
            raise subprocess.CalledProcessError(formatter_result.returncode, blast_formatter_command)

        with open(formatted_output_path, 'rb') as f:
            xml_content = f.read()

        return xml_content

    def parse_blast_xml(self, xml_content):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as xml_file:
            xml_file.write(xml_content)
            xml_file_path = xml_file.name

        with open(xml_file_path) as result_handle:
            blast_records = NCBIXML.parse(result_handle)
            return list(blast_records)

    def extract_best_hits(self, blast_records):
        best_hits = {}
        for record in blast_records:
            best_hsp = None
            for alignment in record.alignments:
                for hsp in alignment.hsps:
                    if best_hsp is None or hsp.score > best_hsp.score:
                        best_hsp = hsp
                        best_hits[record.query] = alignment.hit_id, hsp.sbjct
        return best_hits

    def create_fasta_from_best_hits(self, best_hits):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as fasta_file:
            for query_id, (hit_id, sequence) in best_hits.items():
                fasta_file.write(f">{query_id}\n{sequence}\n".encode())
            fasta_file_path = fasta_file.name

        with open(fasta_file_path, 'rb') as f:
            fasta_content = f.read()

        return fasta_content

    def run_muscle(self, fasta_content):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as fasta_file:
            fasta_file.write(fasta_content)
            fasta_file_path = fasta_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as aligned_fasta_file:
            muscle_command = [
                'muscle',
                '-in', fasta_file_path,
                '-out', aligned_fasta_file.name
            ]

            result = subprocess.run(muscle_command, text=True)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, muscle_command)

        with open(aligned_fasta_file.name, 'rb') as f:
            aligned_fasta_content = f.read()

        return aligned_fasta_content

    def run_fasttree(self, aligned_fasta_content):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as aligned_fasta_file:
            aligned_fasta_file.write(aligned_fasta_content)
            aligned_fasta_file_path = aligned_fasta_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.nwk') as nwk_file:
            fasttree_command = [
                'fasttree',
                '-nt', aligned_fasta_file_path
            ]

            result = subprocess.run(fasttree_command, text=True, stdout=nwk_file)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, fasttree_command)

        with open(nwk_file.name, 'rb') as f:
            nwk_content = f.read()

        return nwk_content

    def create_phylogenetic_tree_analysis(self, from_analysis, fasta_content, aligned_fasta_content, nwk_content, title,
                                          description):
        # Persist the new Analysis object
        phylo_tree_analysis = Analysis.objects.create(
            title=title,
            description=description,
            type=AnalysisTypeChoices.TAXONOMY_TREE,
            status=AnalysisStatusChoices.FINISHED,
            generated_from_analysis=from_analysis,
            experiment=from_analysis.experiment,
        )

        # Save MuscleInput
        muscle_input = MuscleInput.objects.create(
            analysis=phylo_tree_analysis,
            input_file=fasta_content
        )

        # Save MuscleOutput
        MuscleOutput.objects.create(
            analysis=phylo_tree_analysis,
            input=muscle_input,
            output_file=aligned_fasta_content
        )

        # Save FastTreeInput
        fasttree_input = FastTreeInput.objects.create(
            analysis=phylo_tree_analysis,
            input_file=aligned_fasta_content
        )

        # Save FastTreeOutput
        FastTreeOutput.objects.create(
            analysis=phylo_tree_analysis,
            input=fasttree_input,
            output_file=nwk_content
        )

        return phylo_tree_analysis

    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        try:
            analysis = Analysis.objects.get(pk=analysis_id)
        except Analysis.DoesNotExist:
            raise serializers.ValidationError('Analysis not found: try another id')

        if analysis.type != 'HOMOLOGY':
            raise serializers.ValidationError(
                'Analysis type is not "HOMOLOGY"; Taxonomy Tree can only be generated from "HOMOLOGY" analysis')

        serializer = AnalysisTreeSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        try:
            blastn_input = BlastnInput.objects.get(analysis_id=analysis_id)
            homology_output = BlastnOutput.objects.get(input=blastn_input)
        except BlastnInput.DoesNotExist:
            raise serializers.ValidationError('BlastnInput not found for the given analysis id')
        except BlastnOutput.DoesNotExist:
            raise (serializers.ValidationError('BlastnOutput not found for the given BlastnInput'))

        output_file_binary = homology_output.output_file

        # Convert output to XML (outfmt 5)
        xml_content = self.format_blast_output_to_xml(output_file_binary)

        # Parse the BLAST XML output
        blast_records = self.parse_blast_xml(xml_content)

        # Extract the best hits
        best_hits = self.extract_best_hits(blast_records)

        # Create a FASTA file from the best hits
        fasta_content = self.create_fasta_from_best_hits(best_hits)

        # Run muscle to align the sequences
        aligned_fasta_content = self.run_muscle(fasta_content)

        # Run fasttree to generate the phylogenetic tree
        nwk_content = self.run_fasttree(aligned_fasta_content)

        # Persist analysis
        new_analysis = self.create_phylogenetic_tree_analysis(
            analysis,
            fasta_content,
            aligned_fasta_content,
            nwk_content,
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description']
        )

        return Response(data={'nwk': nwk_content.decode('utf-8'), 'analysis_id': new_analysis.id})