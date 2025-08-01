import django_filters
from .models import Experiment, Analysis

class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass

class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass

class ExperimentFilter(django_filters.FilterSet):
    id__in = NumberInFilter(field_name='id', lookup_expr='in')
    title__icontains = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Experiment
        fields = ['id__in', 'title__icontains']

class AnalysisFilter(django_filters.FilterSet):
    id__in = NumberInFilter(field_name='id', lookup_expr='in')
    title__icontains = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    type__in = CharInFilter(field_name='type', lookup_expr='in')
    status__in = CharInFilter(field_name='status', lookup_expr='in')

    class Meta:
        model = Analysis
        fields = ['id__in','title__icontains', 'type__in', 'status__in']