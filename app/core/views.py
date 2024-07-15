from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .serializers import AnalysisSerializer
from .models import Analysis
from injector import inject
from app.pagination import CustomPagination
from app.responses import WrappedResponse
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .filters import GenericQueryParameterListFilter

class AnalysisByIdView(APIView):
    def get(self, request, id):
        return WrappedResponse(
            Analysis.objects.get(id=id), 
            AnalysisSerializer)
    
class AnalysisListView(ListAPIView):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, GenericQueryParameterListFilter]
    ordering_fields = ['id']
    filterset_fields = ['tools']