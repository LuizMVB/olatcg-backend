from django.db import models
from django.utils.translation import gettext as _
from Bio.Align import PairwiseAligner

class AnalysisStatus(models.TextChoices):
    STARTED = 'STARTED', _('Started')
    FAILED = 'FAILED', _('Failed')
    FINISHED = 'FINISHED', _('Finished')
    
class AnalysisType(models.TextChoices):
    ALIGNMENT = 'ALIGNMENT', _('Alignment')
    HOMOLOGY = 'HOMOLOGY', _('Homology')
    TAXONOMY_TREE = 'TAXONOMY_TREE', _('Taxonomy Tree')

class BiopythonBioAlignPairwiseAlignerMode(models.TextChoices):
    GLOBAL = 'global', _('Global')
    LOCAL = 'local', _('Local')
    
class AlignmentType(models.TextChoices):
    GLOBAL = 'GLOBAL', _('Global')
    LOCAL = 'LOCAL', _('Local')

class BiologicalSequenceType(models.TextChoices):
    DNA = 'DNA', _('DNA')
    GAPPED_DNA = 'GAPPED_DNA', _('Gapped DNA')
    RNA = 'RNA', _('RNA')
    GAPPED_RNA = 'GAPPED_RNA', _('Gapped RNA')
    PROTEIN = 'PROTEIN', _('PROTEIN') 
    GAPPED_PROTEIN = 'GAPPED_PROTEIN', _('Gapped Protein')

class Experiment(models.Model):
    title = models.CharField(max_length=20, default=None)
    description = models.CharField(max_length=100, default=None)

class Tool(models.Model):
    title = models.CharField(max_length=20, default='BioPython', unique=True)
    description = models.CharField(max_length=100, default=None)

class Analysis(models.Model):
    title = models.CharField(max_length=20, null=True)
    description = models.CharField(max_length=100, null=True)
    type = models.CharField(
        max_length=13,
        choices=AnalysisType.choices,
        default=AnalysisType.ALIGNMENT
    )
    status = models.CharField(
        max_length=14,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.STARTED,
        blank=True
    )
    tools = models.ManyToManyField(
        Tool, 
        related_name='analyses',
        blank=True
    )
    generated_from_analysis = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL, 
        related_name='generated_analysis',
        null=True,
        default=None,
        blank=True
    )
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.DO_NOTHING,
        related_name='analyses',
        null=True,
        blank=True
    )

class BiopythonBioAlignPairwiseAlignerInput(models.Model):
    mode = models.CharField(
        max_length=6,
        choices=BiopythonBioAlignPairwiseAlignerMode.choices,
        default=BiopythonBioAlignPairwiseAlignerMode.LOCAL
    )
    match_score = models.IntegerField(null=False, default=2)
    mismatch_score = models.IntegerField(null=False, default=-1)
    open_gap_score = models.IntegerField(null=False, default=-2)
    extend_gap_score = models.IntegerField(null=False, default=-1)
    
    analysis = models.OneToOneField(
        Analysis, 
        on_delete=models.DO_NOTHING, 
        related_name='biopython_bio_align_pairwise_aligner_input',
        null=True,
        blank=True
    )

    def calculate_percentage_identity(self):
        matches = sum(1 for a, b in zip(self.target, self.query) if a == b and a != '-')
        total = max(len(self.target), len(self.query))
        percentage_identity = (matches / total) * 100
        return percentage_identity

class BiopythonBioAlignPairwiseAlignerOutput(models.Model):
    score = models.IntegerField(null=True)
    target = models.CharField(max_length=100000, null=True)
    query = models.CharField(max_length=100000, null=True)
    aligned = models.CharField(max_length=1000, null=True)
    shape = models.CharField(max_length=10, null=True)
    
    input = models.ForeignKey(
        BiopythonBioAlignPairwiseAlignerInput,
        on_delete=models.DO_NOTHING,
        related_name='outputs',
        null=True
    )

class BlastnInput(models.Model):
    database = models.CharField(max_length=100, null=False)
    evalue = models.FloatField(null=False)
    gap_open = models.IntegerField(null=False)
    gap_extend = models.IntegerField(null=False)
    penalty = models.IntegerField(null=False)
    input_file = models.BinaryField(null=False)
    analysis = models.OneToOneField(
        Analysis, 
        on_delete=models.DO_NOTHING, 
        related_name='blastn_input',
        null=True,
        blank=True
    )
    
class BlastnOutput(models.Model):
    output_file = models.BinaryField(null=False)
    
    input = models.ForeignKey(
        BlastnInput,
        on_delete=models.DO_NOTHING,
        related_name='outputs',
        null=True
    )
    
class MuscleInput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='muscle_inputs',
        null=True,
        blank=True
    )
    input_file = models.BinaryField(null=True, blank=True)

class MuscleOutput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='muscle_outputs',
        null=True,
        blank=True
    )
    input = models.ForeignKey(
        MuscleInput,
        on_delete=models.DO_NOTHING,
        related_name='outputs',
        null=True
    )
    output_file = models.BinaryField(null=True, blank=True)

class FastTreeInput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='fasttree_inputs',
        null=True,
        blank=True
    )
    input_file = models.BinaryField(null=True, blank=True)

class FastTreeOutput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='fasttree_outputs',
        null=True,
        blank=True
    )
    input = models.ForeignKey(
        FastTreeInput,
        on_delete=models.DO_NOTHING,
        related_name='outputs',
        null=True
    )
    output_file = models.BinaryField(null=True, blank=True)

class Taxonomy(models.Model):
    external_tax_id = models.IntegerField(null=True)
    title = models.CharField(max_length=500, null=True)
    lineage = models.CharField(max_length=100000, null=True)
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.DO_NOTHING,
        related_name='taxonomies',
        null=True,
        blank=True
    )

class Alignment(models.Model):
    taxonomy = models.ForeignKey(
        Taxonomy,
        on_delete=models.DO_NOTHING,
        related_name='alignments',
        null=True
    )
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.DO_NOTHING,
        related_name='alignments',
        null=True,
        blank=True
    )
    
    def align(self, mode, match_score, mismatch_score, open_gap_score, extend_gap_score, biological_sequences):
        aligner = PairwiseAligner()
        
        aligner.mode = mode
        aligner.match_score = match_score
        aligner.mismatch_score = mismatch_score
        aligner.open_gap_score = open_gap_score
        aligner.extend_gap_score = extend_gap_score

        biological_sequences = biological_sequences
        
        alignment_results = aligner.align(
            seqA=biological_sequences[0]['bases'], 
            seqB=biological_sequences[1]['bases'],
        )
        
        return aligner, alignment_results[0]

class BiologicalSequence(models.Model):
    bases = models.CharField(max_length=100000, null=True)
    external_sequence_id = models.CharField(max_length=100, null=True)
    type = models.CharField(
        max_length=14,
        choices=BiologicalSequenceType.choices,
        default=BiologicalSequenceType.DNA 
    )
    alignment = models.ForeignKey(
        Alignment,
        on_delete=models.DO_NOTHING,
        related_name='biological_sequences',
        null=True
    )

class User(models.Model):
    username = models.CharField(max_length=100, null=True)
    password = models.CharField(max_length=100, null=True)