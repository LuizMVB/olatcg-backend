import os, tempfile
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
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
    Experiment
)
from app.pagination import CustomPagination
from app.responses import WrappedResponse
from rest_framework import filters
from rest_framework.response import Response
from .filters import GenericQueryParameterListFilter
from rest_framework import status
from Bio.Blast.Applications import NcbiblastnCommandline

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
    def run_blast(self, query_sequence, db, evalue, gapopen, gapextend, penalty):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as query_file:
            query_file.write(f">query_sequence\n{query_sequence}\n".encode())
            query_file_path = query_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.out') as output_file:
            output_file_path = output_file.name

        blastn_cline = NcbiblastnCommandline(
            query=query_file_path,
            db=db,
            evalue=evalue,
            gapopen=gapopen,
            gapextend=gapextend,
            penalty=penalty,
            outfmt='6 qseqid sseqid pident length qlen slen score evalue qseq sseq',
            out=output_file_path
        )

        stdout, stderr = blastn_cline()
        os.remove(query_file_path)  # Remove the query temporary file

        with open(output_file_path, 'r') as f:
            blast_results = f.readlines()

        os.remove(output_file_path)  # Remove the output temporary file
        return blast_results

    def parse_blast_results(self, blast_results):
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
                    'query_title': '',  # Placeholder for query title if available
                    'query_len': hit['query_length'],
                    'hits': []
                }
            
            parsed_results[query_id]['hits'].append(hit)
        
        # Convert the dictionary to a list of search objects
        return list(parsed_results.values())

    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        request_serializer = AnalysisHomologyRequestSerializer(data=request.data, context={'analysis_id': analysis_id})
    
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        data = request_serializer.data
        all_results = []

        for sequence in data['biological_sequences']:
            bases = sequence.get('bases')
            
            if not bases:
                continue

            blast_results = self.run_blast(bases, 
                                           data['database'],
                                           data['evalue'], 
                                           data['gap_open'], 
                                           data['gap_extend'], 
                                           data['penalty'])
        
            parsed_results = self.parse_blast_results(blast_results)
            
            if len(parsed_results) > 0:
                all_results.extend(parsed_results)

        return Response(all_results, status=status.HTTP_200_OK)

    
# class AnalysisHomologyView(APIView):
#     def load_nodes(self, nodes_file):
#         nodes = {}
#         with open(nodes_file) as f:
#             for line in f:
#                 parts = line.strip().split('|')
#                 tax_id = parts[0].strip()
#                 parent_id = parts[1].strip()
#                 rank = parts[2].strip()
#                 nodes[tax_id] = {'parent': parent_id, 'rank': rank}
#         return nodes

#     def load_names(self, names_file):
#         names = {}
#         with open(names_file) as f:
#             for line in f:
#                 parts = line.strip().split('|')
#                 tax_id = parts[0].strip()
#                 name = parts[1].strip()
#                 name_class = parts[3].strip()
#                 if name_class == "scientific name":
#                     names[tax_id] = name
#         return names

#     def get_lineage(self, tax_id, nodes, names):
#         lineage = []
#         while tax_id != '1':  # Continue while tax_id is not root
#             name = names.get(tax_id, 'unknown')
#             lineage.append(name)
#             if tax_id not in nodes:
#                 break  # Stop if tax_id not found in nodes
#             parent_id = nodes[tax_id]['parent']
#             tax_id = parent_id

#         if tax_id == '1':
#             lineage.append('root')

#         return '; '.join(lineage[::-1])

#     def run_blast(self, query_sequence, db, output_file):
#         with open('temp_query.fasta', 'w') as f:
#             f.write(f">query_sequence\n{query_sequence}\n")
        
#         blastn_cline = NcbiblastnCommandline(
#             query="temp_query.fasta",
#             db=db,
#             evalue=0.001,
#             outfmt=5,  # Formato de saída XML
#             out=output_file
#         )
        
#         stdout, stderr = blastn_cline()
#         os.remove('temp_query.fasta')  # Remove the temporary file

#         temp_output_file = tempfile.NamedTemporaryFile(delete=False).name
#         shutil.copyfile(output_file, temp_output_file)
#         os.remove(output_file)
        
#         return temp_output_file

#     def parse_blast_output(self, blast_output, nodes, names):
#         with open(blast_output) as result_handle:
#             blast_records = NCBIXML.parse(result_handle)
            
#             results = []
            
#             for blast_record in blast_records:
#                 record = {
#                     'query': blast_record.query,
#                     'alignments': []
#                 }
#                 for alignment in blast_record.alignments:
#                     accession = alignment.accession
#                     tax_id = alignment.hit_id.split("|")[-1]
#                     taxonomy_lineage = self.get_lineage(tax_id, nodes, names)
                    
#                     alignment_data = {
#                         'title': alignment.title,
#                         'length': alignment.length,
#                         'taxonomy': taxonomy_lineage,
#                         'hsps': []
#                     }
#                     for hsp in alignment.hsps:
#                         hsp_data = {
#                             'evalue': hsp.expect,
#                             'query_seq': hsp.query,
#                             'match_seq': hsp.match,
#                             'subject_seq': hsp.sbjct
#                         }
#                         alignment_data['hsps'].append(hsp_data)
#                     record['alignments'].append(alignment_data)
#                 results.append(record)
            
#             return results

#     @transaction.atomic
#     def post(self, request, analysis_id, *args, **kwargs):
#         data = request.data
#         database_key = data.get('database', 'default')
#         biological_sequences = data.get('biological_sequences', [])
        
#         db_path = BLAST_DB_PATHS.get(database_key)
#         if not db_path:
#             return Response({'error': 'Invalid database specified'}, status=400)
        
#         nodes_file = NODES_FILE
#         names_file = NAMES_FILE
#         nodes = self.load_nodes(nodes_file)
#         names = self.load_names(names_file)
        
#         all_results = []

#         for sequence in biological_sequences:
#             bases = sequence.get('bases')
#             if not bases:
#                 continue
            
#             blast_output_file = f"blast_output_{bases[:10]}.xml"
#             blast_output = self.run_blast(bases, db_path, blast_output_file)
#             results = self.parse_blast_output(blast_output, nodes, names)
#             all_results.extend(results)
        
#         results_json = json.dumps(all_results, indent=4)
        
#         return Response(json.loads(results_json))