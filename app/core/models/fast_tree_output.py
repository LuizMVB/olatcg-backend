from django.db import models

from core.models import Analysis, FastTreeInput

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