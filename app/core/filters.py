import django_filters
from .models import Experiment, Analysis

class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass

class ExperimentFilter(django_filters.FilterSet):
    id__in = NumberInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = Experiment
        fields = ['id__in']

class AnalysisFilter(django_filters.FilterSet):
    id__in = NumberInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = Analysis
        fields = ['id__in']