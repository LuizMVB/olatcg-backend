from django.db import transaction
from rest_framework.views import APIView
from app.responses import WrappedResponse
from rest_framework.response import Response
from rest_framework import status
from core.serializers import AnalysisAlignmentRequestSerializer, AnalysisSerializer
from core.models import Analysis, Alignment, BiologicalSequence, BiopythonBioAlignPairwiseAlignerInput, BiopythonBioAlignPairwiseAlignerOutput

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