from rest_framework import serializers
from .models import Taxonomy, Alignment, Analysis, Tool

class AlignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alignment
        fields = '__all__'

class TaxonomySerializer(serializers.ModelSerializer):
    alignments = AlignmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Taxonomy
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        for aln in representation['alignments']:
            aln.pop('analysis')
            aln.pop('taxonomy')
        
        return representation

class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = '__all__'

class AnalysisSerializer(serializers.ModelSerializer):
    tools = ToolSerializer(many=True, read_only=True)
    taxonomies = TaxonomySerializer(many=True, read_only=True)
    alignments = AlignmentSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if representation['taxonomies']:
            representation.pop('alignments')

            for tax in representation['taxonomies']:
                tax.pop('analysis')

            return representation
        
        if representation['alignments']:
            representation.pop('taxonomies')

            for aln in representation['alignments']:
                aln.pop('analysis')
                aln.pop('taxonomy')
            
            return representation
        
        return representation