from django.db import models
from core.models import Analysis

class MuscleInput(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='muscle_inputs', null=True, blank=True)
    input_file = models.BinaryField(null=True, blank=True)