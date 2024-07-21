from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from .serializers import AnalysisSerializer, AnalysisAlignmentRequestSerializer, ExperimentSerializer
from .models import Analysis, Alignment, BiologicalSequence, BiopythonBioAlignPairwiseAlignerInput, BiopythonBioAlignPairwiseAlignerOutput, Experiment
from app.pagination import CustomPagination
from app.responses import WrappedResponse
from rest_framework import filters
from rest_framework.response import Response
from .filters import GenericQueryParameterListFilter
from rest_framework import status
import json
from Bio.Blast.Applications import NcbiblastnCommandline
from Bio.Blast import NCBIXML
import os, tempfile, shutil
from .constants import BLAST_DB_PATHS

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
        request_serializer = AnalysisAlignmentRequestSerializer(data=request.data, context={'analysis_id': analysis_id})
        
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
        
        return '; '.join(lineage[::-1]) 

    def run_blast(self, query_sequence, db):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as query_file:
            query_file.write(f">query_sequence\n{query_sequence}\n".encode())
            query_file_path = query_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as output_file:
            output_file_path = output_file.name
        
        blastn_cline = NcbiblastnCommandline(
            query=query_file_path,
            db=db,
            evalue=0.001,
            outfmt='15',  # Formato de saída JSON detalhado com informações taxonômicas
            out=output_file_path
        )
        
        stdout, stderr = blastn_cline()
        os.remove(query_file_path)  # Remove o arquivo temporário de consulta
        
        with open(output_file_path, 'r') as f:
            blast_results = json.load(f)
        
        os.remove(output_file_path)  # Remove o arquivo de saída temporário
        return blast_results

    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        data = request.data
        database_key = data.get('database', 'default')
        biological_sequences = data.get('biological_sequences', [])
        
        db_path = BLAST_DB_PATHS.get(database_key)
        if not db_path:
            return Response({'error': 'Invalid database specified'}, status=400)
        
        all_results = []

        for sequence in biological_sequences:
            bases = sequence.get('bases')
            if not bases:
                continue
            
            blast_results = self.run_blast(bases, db_path)
            all_results.append(blast_results)
        
        return Response(all_results)