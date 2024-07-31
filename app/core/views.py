import os, tempfile, subprocess
from django.db import transaction
from django.core.files import File
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from app.pagination import CustomPagination
from app.responses import WrappedResponse
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status
from .filters import GenericQueryParameterListFilter
from .serializers import (
    AnalysisSerializer, 
    AnalysisAlignmentRequestSerializer, 
    ExperimentSerializer, 
    AnalysisHomologyRequestSerializer
)
from .models import (
    Analysis, 
    Alignment, 
    BiologicalSequence, 
    BiopythonBioAlignPairwiseAlignerInput, 
    BiopythonBioAlignPairwiseAlignerOutput, 
    Experiment,
    BlastnInput,
    BlastnOutput
)

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
    filterset_fields = ['id', 'experiment']
        
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
        
        for aln_result in aln_output_info:
            BiopythonBioAlignPairwiseAlignerOutput.objects.create(
                input=bio_python_aligner_input,
                score=aln_result.score,
                target=aln_result.target,
                query=aln_result.query,
                aligned=aln_result.aligned,
                shape=aln_result.shape
            )
        
        response_serializer = AnalysisSerializer(analysis)
        
        return WrappedResponse(
            response_serializer.data, 
            status.HTTP_201_CREATED)

class AnalysisHomologyView(APIView):
    
    def create_temp_file(self, content, suffix):
        """Helper function to create a temporary file."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content.encode())
        temp_file_path = temp_file.name
        temp_file.close()
        return temp_file_path

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

    def parse_blast_results(self, blast_results, query_titles):
        """Parses the BLAST results into a structured format."""
        parsed_results = {}
        for line in blast_results:
            cols = line.strip().split("\t")
            query_id = cols[0]
            hit = {
                'subject_id': cols[1],
                'percent_identity': float(cols[2]),
                'alignment_length': int(cols[3]),
                'query_length': int(cols[4]),
                'subject_length': int(cols[5]),
                'score': float(cols[6]),
                'evalue': float(cols[7]),
                'query_sequence': cols[8],
                'subject_sequence': cols[9]
            }

            if query_id not in parsed_results:
                parsed_results[query_id] = {
                    'query_id': query_id,
                    'query_title': query_titles.get(query_id, ''),  # Get query title from the dictionary
                    'query_len': hit['query_length'],
                    'hits': []
                }

            parsed_results[query_id]['hits'].append(hit)

        return list(parsed_results.values())

    def perform_homology_analysis(self, data, all_results, query_titles, query_file_path):
        blast_outfmt11_path = self.run_blast(query_file_path,
                                            data['database'],
                                            data['evalue'],
                                            data['gap_open'],
                                            data['gap_extend'],
                                            data['penalty'])
            
        blast_outfmt6_path = self.format_blast_output(blast_outfmt11_path)

        with open(blast_outfmt6_path, 'r') as f:
            blast_results = f.readlines()

        parsed_results = self.parse_blast_results(blast_results, query_titles)
        
        if len(parsed_results) > 0:
            all_results.extend(parsed_results)
            
        return blast_outfmt11_path,blast_outfmt6_path

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

        blast_outfmt11_path, blast_outfmt6_path = self.perform_homology_analysis(
            data, all_results, query_titles, query_file_path)
        
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