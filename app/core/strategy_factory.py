from .strategies import (
    AnalysisExecutionStrategy,
    PairwiseAlignmentStrategy,
    HomologySearchStrategy,
    TaxonomyTreeStrategy
)
from .models import AnalysisTypeChoices


class StrategyFactory:
    _strategies = {
        AnalysisTypeChoices.PAIRWISE_ALIGNMENT: PairwiseAlignmentStrategy(),
        AnalysisTypeChoices.HOMOLOGY_SEARCH: HomologySearchStrategy(),
        AnalysisTypeChoices.TAXONOMY_TREE: TaxonomyTreeStrategy(),
    }

    @staticmethod
    def get_strategy(analysis_type) -> AnalysisExecutionStrategy:
        strategy = StrategyFactory._strategies.get(analysis_type)
        if not strategy:
            raise ValueError(f"No strategy defined for analysis type: {analysis_type}")
        return strategy