from django.db import models
from core.models.analysis import Analysis

class MuscleInput(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='muscle_inputs', null=True, blank=True)
    input_file = models.CharField(max_length=100, null=True, blank=True)