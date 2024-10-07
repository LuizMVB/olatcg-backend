from django.db import models
from core.models.biopython_bio_align_pairwise_aligner_mode_choices import BiopythonBioAlignPairwiseAlignerModeChoices
from core.models.analysis import Analysis

class BiopythonBioAlignPairwiseAlignerInput(models.Model):
    mode = models.CharField(
        max_length=6,
        choices=BiopythonBioAlignPairwiseAlignerModeChoices.choices,
        default=BiopythonBioAlignPairwiseAlignerModeChoices.LOCAL
    )
    match_score = models.IntegerField(null=False, default=2)
    mismatch_score = models.IntegerField(null=False, default=-1)
    open_gap_score = models.IntegerField(null=False, default=-2)
    extend_gap_score = models.IntegerField(null=False, default=-1)
    analysis = models.OneToOneField(Analysis, on_delete=models.DO_NOTHING, related_name='biopython_input', null=True, blank=True)
