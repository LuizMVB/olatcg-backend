from rest_framework.views import APIView
from app.responses import WrappedResponse
from rest_framework.response import Response
from rest_framework import status

from core.models import Analysis
from core.serializers import AnalysisSerializer


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