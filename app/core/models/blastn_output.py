from django.db import models
from core.models.blastn_input import BlastnInput

class BlastnOutput(models.Model):
    output_file = models.BinaryField(null=False)
    input = models.ForeignKey(BlastnInput, on_delete=models.DO_NOTHING, related_name='outputs', null=True)
