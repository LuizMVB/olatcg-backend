from rest_framework import serializers
from .models import (
    Taxonomy, Alignment, Analysis, 
    BiologicalSequence, Experiment, 
    BiopythonBioAlignPairwiseAlignerInput, 
    BiopythonBioAlignPairwiseAlignerOutput,
    Tool
)

class BiologicalSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicalSequence
        fields = '__all__'
        
class AnalysisAlignmentRequestSerializer(serializers.Serializer):
    mode = serializers.CharField()
    match_score = serializers.IntegerField()
    mismatch_score = serializers.IntegerField()
    open_gap_score = serializers.IntegerField()
    extend_gap_score = serializers.IntegerField()
    biological_sequences = BiologicalSequenceSerializer(many=True)
    
    def validate(self, data):
        analysis_id = int(self.context.get('analysis_id'))
        
        try:            
            analysis = Analysis.objects.get(pk=analysis_id)
        except:
            raise serializers.ValidationError('Analysis not found: try another id')
            
        if analysis.type != 'ALIGNMENT':
            raise serializers.ValidationError('Analysis\' type is not equals to "ALIGNMENT"')
    
        return super().validate(data)
    
class BiopythonBioAlignPairwiseAlignerOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiopythonBioAlignPairwiseAlignerOutput
        fields = '__all__'

class BiopythonBioAlignPairwiseAlignerInputSerializer(serializers.ModelSerializer):
    outputs = BiopythonBioAlignPairwiseAlignerOutputSerializer(many=True)
    
    class Meta:
        model = BiopythonBioAlignPairwiseAlignerInput
        fields = '__all__'

class AlignmentSerializer(serializers.ModelSerializer):
    biological_sequences = BiologicalSequenceSerializer(many=True, read_only=True)

    class Meta:
        model = Alignment
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'biological_sequences' in representation:
            for bio_seq in representation['biological_sequences']:
                bio_seq.pop('alignment')
        return representation

class TaxonomySerializer(serializers.ModelSerializer):
    alignments = AlignmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Taxonomy
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'alignments' in representation:
            for aln in representation['alignments']:
                aln.pop('analysis')
                aln.pop('taxonomy')
        return representation

class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = '__all__'

class AnalysisSerializer(serializers.ModelSerializer):
    taxonomies = TaxonomySerializer(many=True, read_only=True)
    alignments = AlignmentSerializer(many=True, read_only=True)
    biopython_bio_align_pairwise_aligner_input = BiopythonBioAlignPairwiseAlignerInputSerializer(required=False)
    tool = ToolSerializer(read_only=True)
    experiment = serializers.PrimaryKeyRelatedField(queryset=Experiment.objects.all(), required=False)
    generated_from_analysis = serializers.PrimaryKeyRelatedField(queryset=Analysis.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Analysis
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if 'taxonomies' in representation and representation['taxonomies']:
            representation.pop('biopython_bio_align_pairwise_aligner_input', None)
            representation.pop('alignments', None)

            for tax in representation['taxonomies']:
                tax.pop('analysis')

            return representation
        
        if 'alignments' in representation and representation['alignments']:
            representation.pop('taxonomies', None)
            if 'biopython_bio_align_pairwise_aligner_input' in representation:
                representation['biopython_bio_align_pairwise_aligner_input'].pop('analysis')

            for aln in representation['alignments']:
                aln.pop('analysis')
                aln.pop('taxonomy')
            
            return representation
        
        representation.pop('taxonomies', None)
        representation.pop('alignments', None)
        representation.pop('biopython_bio_align_pairwise_aligner_input', None)
        representation.pop('tool', None)

        return representation

    def validate(self, data):
        experiment_id = int(self.context.get('experiment_id'))
        
        if experiment_id is not None:
            try:
                Experiment.objects.get(id=experiment_id)
            except Experiment.DoesNotExist:
                raise serializers.ValidationError('Experiment not found: try another id')
    
        return super().validate(data)
    
class ExperimentSerializer(serializers.ModelSerializer):
    analyses = AnalysisSerializer(many=True, required=False)
    
    class Meta:
        model = Experiment
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if representation['analyses']:
            for analysis in representation['analyses']:
                analysis.pop('experiment')
        
            return representation
        
        representation.pop('analyses')

        return representation
            