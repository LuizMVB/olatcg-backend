from rest_framework.generics import ListCreateAPIView
from app.pagination import CustomPagination
from rest_framework import filters
from core.filters import GenericQueryParameterListFilter
from core.serializers import *
from core.models import *
from django.db import transaction

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