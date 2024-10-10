from django.db import models
from django.utils.translation import gettext as _

class AnalysisStatusChoices(models.TextChoices):
    WAITING_FOR_EXECUTION = 'WAITING_FOR_EXECUTION', _('Waiting for execution')
    IN_EXECUTION = 'IN_EXECUTION', _('In Execution')
    EXECUTION_FAILED = 'EXECUTION_FAILED', _('Execution Failled')
    EXECUTION_SUCCEEDED = 'EXECUTION_SUCCEEDED', _('Execution Succeeded')
