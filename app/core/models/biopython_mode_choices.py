from django.db import models
from django.utils.translation import gettext as _

class BiopythonBioAlignPairwiseAlignerModeChoices(models.TextChoices):
    GLOBAL = 'global', _('Global')
    LOCAL = 'local', _('Local')
