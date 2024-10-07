from django.db import models
from core.models.analysis import Analysis

class BlastnInput(models.Model):
    database = models.CharField(max_length=100, null=False)
    evalue = models.FloatField(null=False)
    gap_open = models.IntegerField(null=False)
    gap_extend = models.IntegerField(null=False)
    penalty = models.IntegerField(null=False)
    input_file = models.BinaryField(null=False)
    analysis = models.OneToOneField(Analysis,
                                    on_delete=models.DO_NOTHING,
                                    related_name='blastn_input',
                                    null=True, blank=True)
