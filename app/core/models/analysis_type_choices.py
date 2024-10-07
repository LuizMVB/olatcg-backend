from django.db import models
from django.utils.translation import gettext as _

class AnalysisTypeChoices(models.TextChoices):
    ALIGNMENT = 'ALIGNMENT', _('Alignment')
    HOMOLOGY = 'HOMOLOGY', _('Homology')
    TAXONOMY_TREE = 'TAXONOMY_TREE', _('Taxonomy Tree')
