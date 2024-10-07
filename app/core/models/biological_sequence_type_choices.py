from django.db import models
from django.utils.translation import gettext as _

class BiologicalSequenceTypeChoices(models.TextChoices):
    DNA = 'DNA', _('DNA')
    GAPPED_DNA = 'GAPPED_DNA', _('Gapped DNA')
    RNA = 'RNA', _('RNA')
    GAPPED_RNA = 'GAPPED_RNA', _('Gapped RNA')
    PROTEIN = 'PROTEIN', _('Protein')
    GAPPED_PROTEIN = 'GAPPED_PROTEIN', _('Gapped Protein')
