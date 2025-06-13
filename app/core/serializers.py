from rest_framework import serializers
from .models import Experiment, Analysis, AnalysisInput, AnalysisOutput

class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = ['id', 'title', 'description']
        read_only_fields = ['id']

class AnalysisOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisOutput
        fields = ['id', 'results', 'file']


class AnalysisInputSerializer(serializers.ModelSerializer):
    outputs = AnalysisOutputSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisInput
        fields = ['id', 'command', 'outputs']


class AnalysisSerializer(serializers.ModelSerializer):
    inputs = AnalysisInputSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = [
            'id',
            'title',
            'description',
            'type',
            'status',
            'generated_from_analysis',
            'parameters',
            'inputs',
        ]
        read_only_fields = ['experiment', 'status']