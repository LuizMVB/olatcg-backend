from django.db import models
from core.models import Analysis, MuscleInput

class MuscleOutput(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='muscle_outputs', null=True, blank=True)
    input = models.ForeignKey(MuscleInput, on_delete=models.DO_NOTHING, related_name='outputs', null=True)
    output_file = models.BinaryField(null=True, blank=True)
