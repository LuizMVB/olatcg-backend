from django.db import models
from Bio.Align import PairwiseAligner
from core.models import Taxonomy, Analysis

class Alignment(models.Model):
    taxonomy = models.ForeignKey(
        Taxonomy,
        on_delete=models.DO_NOTHING,
        related_name='alignments',
        null=True
    )
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.DO_NOTHING,
        related_name='alignments',
        null=True,
        blank=True
    )

    def align(self, mode, match_score, mismatch_score, open_gap_score, extend_gap_score, biological_sequences):
        aligner = PairwiseAligner()

        aligner.mode = mode
        aligner.match_score = match_score
        aligner.mismatch_score = mismatch_score
        aligner.open_gap_score = open_gap_score
        aligner.extend_gap_score = extend_gap_score

        biological_sequences = biological_sequences

        alignment_results = aligner.align(
            seqA=biological_sequences[0]['bases'],
            seqB=biological_sequences[1]['bases'],
        )

        return aligner, alignment_results[0]