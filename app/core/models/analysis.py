from django.db import models

from core.models.analysis_type_choices import AnalysisTypeChoices
from core.models.analysis_status_choices import AnalysisStatusChoices
from core.models.experiment import Experiment
from core.models.tool import Tool

class Analysis(models.Model):
    title = models.CharField(max_length=20, null=True)
    description = models.CharField(max_length=100, null=True)
    type = models.CharField(
        max_length=13,
        choices=AnalysisTypeChoices.choices,
        default=AnalysisTypeChoices.ALIGNMENT
    )
    status = models.CharField(
        max_length=14,
        choices=AnalysisStatusChoices.choices,
        default=AnalysisStatusChoices.STARTED,
        blank=True
    )
    tools = models.ManyToManyField(Tool, related_name='analyses', blank=True)
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
