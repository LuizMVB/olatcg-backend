from django.db import transaction
from rest_framework.generics import ListCreateAPIView
from app.pagination import CustomPagination
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status
from core.filters import GenericQueryParameterListFilter
from core.models import Analysis, Experiment
from core.serializers import AnalysisSerializer


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