import os, tempfile, subprocess
from Bio.Blast import NCBIXML
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from app.pagination import CustomPagination
from app.responses import WrappedResponse
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status
from .filters import GenericQueryParameterListFilter
from .constants import *
from .serializers import *
from .models import *

class ExperimentListCreateView(ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter, GenericQueryParameterListFilter]
    ordering_fields = ['id']
    filterset_fields = ['id', 'analysis']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
        
class AnalysisListView(ListAPIView):
    queryset = Analysis.objects.all().order_by('id')
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter, GenericQueryParameterListFilter]
    ordering_fields = ['id']
    filterset_fields = ['id', 'experiment', 'type']
        
class AnalysisByExperimentListCreateView(ListCreateAPIView):
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter, GenericQueryParameterListFilter]
    ordering_fields = ['id']
    filterset_fields = ['id', 'experiment']

    def get_queryset(self):
        experiment_id = self.kwargs['experiment_id']
        return Analysis.objects.filter(experiment_id=experiment_id).order_by('id')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        experiment_id = self.kwargs['experiment_id']
        serializer = self.get_serializer(data=request.data, 
                                         context={'experiment_id': experiment_id})
        if serializer.is_valid():
            experiment = Experiment.objects.get(id=experiment_id)
            serializer.save(experiment=experiment)
            return Response(serializer.data, 
                            status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, 
                    status.HTTP_400_BAD_REQUEST, 
                    AnalysisSerializer)

class AnalysisByIdView(APIView):
    def get(self, request, id):
        try:
            return WrappedResponse(
                Analysis.objects.get(id=id),
                status.HTTP_200_OK,
                AnalysisSerializer)
        except Analysis.DoesNotExist:
            return Response(
                    {"error": "Analysis not found"}, 
                    status.HTTP_404_NOT_FOUND,
                    AnalysisSerializer)
    
class AnalysisAlignmentView(APIView):
    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        request_serializer = AnalysisAlignmentRequestSerializer(data=request.data, 
                                                                context={'analysis_id': analysis_id})
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors, 
                status.HTTP_400_BAD_REQUEST)
    
        analysis = Analysis.objects.get(id=analysis_id)
        alignment = Alignment.objects.create(analysis=analysis)
        data = request_serializer.validated_data
        
        for seq_data in data['biological_sequences']:
            BiologicalSequence.objects.create(alignment=alignment, **seq_data)
        
        aln_input_info, aln_output_info = alignment.align(**data)
                
        bio_python_aligner_input = BiopythonBioAlignPairwiseAlignerInput.objects.create(
            analysis=analysis,
            mode=aln_input_info.mode,
            match_score=aln_input_info.match_score,
            mismatch_score=aln_input_info.mismatch_score,
            open_gap_score=aln_input_info.open_gap_score,
            extend_gap_score=aln_input_info.extend_gap_score
        )

        BiopythonBioAlignPairwiseAlignerOutput.objects.create(
            input=bio_python_aligner_input,
            score=aln_output_info.score,
            target=aln_output_info.target,
            query=aln_output_info.query,
            aligned=aln_output_info.aligned,
            shape=aln_output_info.shape
        )
        
        response_serializer = AnalysisSerializer(analysis)
        
        return WrappedResponse(
            response_serializer.data, 
            status.HTTP_201_CREATED)

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
            raise subprocess.CalledProcessError(result.returncode, blastn_command, output=result.stdout, stderr=result.stderr)

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
            raise subprocess.CalledProcessError(formatter_result.returncode, blast_formatter_command, output=formatter_result.stdout, stderr=formatter_result.stderr)

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
                type=BiologicalSequenceType.GAPPED_DNA
            ))
            
            biological_sequences.append(BiologicalSequence(
                alignment=alignment,
                bases=subject_seq,
                external_sequence_id=subject_id,
                type=BiologicalSequenceType.GAPPED_DNA
            ))

        Taxonomy.objects.bulk_create(taxonomies)
        Alignment.objects.bulk_create(alignments)
        BiologicalSequence.objects.bulk_create(biological_sequences)

        return list(parsed_results.values())

    def perform_homology_analysis(self, data, analysis, all_results, query_titles, query_file_path, taxid_map, nodes, names):
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

    def create_phylogenetic_tree_analysis(self, from_analysis, fasta_content, aligned_fasta_content, nwk_content, title, description):
        # Persist the new Analysis object
        phylo_tree_analysis = Analysis.objects.create(
            title=title,
            description=description,
            type=AnalysisType.TAXONOMY_TREE,
            status=AnalysisStatus.FINISHED,
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
            raise serializers.ValidationError('Analysis type is not "HOMOLOGY"; Taxonomy Tree can only be generated from "HOMOLOGY" analysis')

        serializer = AnalysisTreeSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        
        try:
            blastn_input = BlastnInput.objects.get(analysis_id=analysis_id)
            homology_output = BlastnOutput.objects.get(input=blastn_input)
        except BlastnInput.DoesNotExist:
            raise serializers.ValidationError('BlastnInput not found for the given analysis id')
        except BlastnOutput.DoesNotExist:
            raise(serializers.ValidationError('BlastnOutput not found for the given BlastnInput'))

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