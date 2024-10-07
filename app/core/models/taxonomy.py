from django.db import models
from core.models import Analysis

class Taxonomy(models.Model):
    external_tax_id = models.IntegerField(null=True)
    title = models.CharField(max_length=500, null=True)
    lineage = models.CharField(max_length=100000, null=True)
    analysis = models.ForeignKey(Analysis, on_delete=models.DO_NOTHING, related_name='taxonomies', null=True, blank=True)
