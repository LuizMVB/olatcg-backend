from django.db import models

from core.models import Analysis


class FastTreeInput(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='fasttree_inputs',
        null=True,
        blank=True
    )
    input_file = models.BinaryField(null=True, blank=True)