from django.db import models

from core.models.analysis import Analysis
from core.models.fast_tree_input import FastTreeInput

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