from django.db import models
from core.models.muscle_input import MuscleInput

class MuscleOutput(models.Model):
    input = models.ForeignKey(MuscleInput, on_delete=models.DO_NOTHING, related_name='outputs', null=True)
    output_file = models.CharField(max_length=100, null=True, blank=True)
