from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Experiment, Analysis, AnalysisStatusChoices, AnalysisInput, AnalysisOutput
from .serializers import ExperimentSerializer, AnalysisSerializer
from .filters import ExperimentFilter, AnalysisFilter
from .strategy_factory import StrategyFactory
from .strategies import ExecutionType

class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    filterset_class = ExperimentFilter
    ordering_fields = ['id', 'created_at']
    ordering = ['-id']

class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    filterset_class = AnalysisFilter
    ordering_fields = ['id']
    ordering = ['-id']

    def get_queryset(self):
        experiment_id = self.kwargs.get('experiment_pk')
        return Analysis.objects.filter(experiment_id=experiment_id)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            experiment_id = self.kwargs.get('experiment_pk')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            experiment = Experiment.objects.get(pk=experiment_id)
            analysis = serializer.save(experiment=experiment)

            strategy = StrategyFactory.get_strategy(analysis.type)
            execution = strategy.execute(analysis)

            if execution.type is ExecutionType.ASYNC:
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            analysis.status = AnalysisStatusChoices.SUCCEEDED
            analysis.save()

            analysis_input = AnalysisInput.objects.create(
                command=execution.command,
                analysis=analysis
            )

            AnalysisOutput.objects.create(
                results=execution.result,
                file=None,
                input=analysis_input
            )

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            analysis.status = AnalysisStatusChoices.FAILED
            raise e