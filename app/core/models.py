from django.db import models
from django.utils.translation import gettext as _

class AnalysisStatus(models.TextChoices):
    STARTED = 'STARTED', _('Started')
    FAILED = 'FAILED', _('Failed')
    FINISHED = 'FINISHED', _('Finished')

class AlignmentType(models.TextChoices):
    GLOBAL = 'GLOBAL', _('Global')
    LOCAL = 'LOCAL', _('Local')

class BiologicalSequenceType(models.TextChoices):
    DNA = 'DNA', _('DNA')
    RNA = 'RNA', _('RNA')
    PROTEIN = 'PROTEIN', _('PROTEIN') 

class Tool(models.Model):
    title = models.CharField(max_length=20, default='ALIGNMENT', unique=True)
    description = models.CharField(max_length=100, default=None)

class Analysis(models.Model):
    title = models.CharField(max_length=20, null=True)
    description = models.CharField(max_length=100, null=True)
    status = models.CharField(
        max_length=14,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.STARTED
    )
    tools = models.ManyToManyField(Tool, related_name='analyses')

class HomologyAnalysis(models.Model):
    newick = models.CharField(max_length=700, null=True)
    coefficiente_of_variation = models.FloatField(null=True)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, primary_key=True)


class AlignmentAnalysis(models.Model):
    query_external_id = models.CharField(max_length=100, null=True)
    target_external_id = models.CharField(max_length=100, null=True)
    similarity = models.FloatField(null=True)
    score = models.FloatField(null=True)
    identity_percentage = models.FloatField(null=True)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, primary_key=True)


class Taxonomy(models.Model):
    name = models.CharField(max_length=500, null=True)
    description = models.CharField(max_length=100000, null=True)
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.DO_NOTHING,
        related_name='taxonomies',
        null=True
    )

class Alignment(models.Model):
    type = models.CharField(
        max_length=6,
        choices=AlignmentType.choices,
        default=AlignmentType.LOCAL
    )
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
        null=True
    )
    

class BiologicalSequence(models.Model):
    bases = models.CharField(max_length=100000, null=True)
    country_origin = models.CharField(max_length=100, null=True)
    external_database_id = models.CharField(max_length=100, null=True)
    type = models.CharField(
        max_length=7,
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