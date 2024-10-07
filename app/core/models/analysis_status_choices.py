from django.db import models
from django.utils.translation import gettext as _

class AnalysisStatusChoices(models.TextChoices):
    STARTED = 'STARTED', _('Started')
    FAILED = 'FAILED', _('Failed')
    FINISHED = 'FINISHED', _('Finished')
