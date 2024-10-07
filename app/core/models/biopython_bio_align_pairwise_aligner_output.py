from django.db import models
from core.models import BiopythonBioAlignPairwiseAlignerInput

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