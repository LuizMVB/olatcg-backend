from django.db import models

from core.models.analysis import Analysis


class FastTreeInput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='fasttree_inputs',
        null=True,
        blank=True
    )
    input_file = models.CharField(max_length=100, null=True, blank=True)