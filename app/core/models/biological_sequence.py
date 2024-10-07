from django.db import models
from core.models.biological_sequence_type_choices import BiologicalSequenceTypeChoices
from core.models.alignment import Alignment

class BiologicalSequence(models.Model):
    bases = models.CharField(max_length=100000, null=True)
    external_sequence_id = models.CharField(max_length=100, null=True)
    type = models.CharField(
        max_length=14,
        choices=BiologicalSequenceTypeChoices.choices,
        default=BiologicalSequenceTypeChoices.DNA
    )
    alignment = models.ForeignKey(
        Alignment,
        on_delete=models.DO_NOTHING,
        related_name='biological_sequences',
        null=True
    )