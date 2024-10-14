from django.db import models

from core.models.fast_tree_input import FastTreeInput

class FastTreeOutput(models.Model):
    input = models.ForeignKey(
        FastTreeInput,
        on_delete=models.DO_NOTHING,
        related_name='outputs',
        null=True
    )
    output_file = models.CharField(max_length=100, null=True, blank=True)