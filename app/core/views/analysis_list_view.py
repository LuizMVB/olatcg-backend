from rest_framework.generics import ListAPIView
from app.pagination import CustomPagination
from rest_framework import filters
from core.filters import GenericQueryParameterListFilter
from core.models import Analysis
from core.serializers import AnalysisSerializer


class AnalysisListView(ListAPIView):
    queryset = Analysis.objects.all().order_by('id')
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter, GenericQueryParameterListFilter]
    ordering_fields = ['id']
    filterset_fields = ['id', 'experiment', 'type']