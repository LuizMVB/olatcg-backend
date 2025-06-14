from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth.models import User

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Experiment(TimestampedModel):
    title = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=500, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments')

class AnalysisTypeChoices(models.TextChoices):
    PAIRWISE_ALIGNMENT = 'PAIRWISE_ALIGNMENT', _('Pairwise Alignment')
    HOMOLOGY_SEARCH = 'HOMOLOGY_SEARCH', _('Homology Search')
    TAXONOMY_TREE = 'TAXONOMY_TREE', _('Taxonomy Tree')

class AnalysisStatusChoices(models.TextChoices):
    WAITING = 'WAITING', _('Waiting')
    STARTED = 'STARTED', _('Started')
    FAILED = 'FAILED', _('Failled')
    SUCCEEDED = 'SUCCEEDED', _('Succeeded')

class Analysis(TimestampedModel):
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.CharField(max_length=500, null=True)
    type = models.CharField(
        max_length=18,
        choices=AnalysisTypeChoices.choices
    )
    status = models.CharField(
        max_length=9,
        choices=AnalysisStatusChoices.choices,
        default=AnalysisStatusChoices.WAITING,
        blank=True
    )
    generated_from_analysis = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        related_name='generated_analysis',
        null=True,
        default=None
    )
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name='analyses',
        null=False
    )
    parameters = models.JSONField(null=False, blank=False)

class AnalysisInput(TimestampedModel):
    command = models.CharField(max_length=5000, null=True)
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='inputs',
        null=False
    )

class AnalysisOutput(TimestampedModel):
    results = models.JSONField(null=False)
    file = models.CharField(max_length=1000, null=True)
    input = models.ForeignKey(
        AnalysisInput,
        on_delete=models.CASCADE,
        related_name='outputs',
        null=False
    )
