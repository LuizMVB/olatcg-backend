from abc import ABC, abstractmethod
from Bio.Align import PairwiseAligner
from .models import Analysis
from .constants import PAIRWISE_ALIGNMENT_COMMAND_TEMPLATE, BLAST_DB_PATHS, BLASTN_EXCHANGE, BLASTN_ROUTING_KEY
from .rabbitmq_producer import RabbitmqPublisher
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ExecutionType(str, Enum):
    SYNC = "SYNC"
    ASYNC = "ASYNC"

@dataclass
class AnalysisExecutionResult:
    command: Optional[str] = None
    result: object = None
    file: Optional[str] = None
    type: ExecutionType = ExecutionType.SYNC

class AnalysisExecutionStrategy(ABC):
    def execute(self, analysis: Analysis) -> AnalysisExecutionResult:
        required_keys = self._define_required_keys()
        self._validate_parameters(analysis.parameters, required_keys)
        return self._perform_analysis(analysis)

    def _validate_parameters(self, parameters: dict, required_keys: dict):
        errors = []
        for key, expected_type in required_keys.items():
            if key not in parameters:
                errors.append(f"Missing required parameter: {key}")
                continue

            if not isinstance(parameters[key], expected_type):
                type_names = (
                    expected_type.__name__ if isinstance(expected_type, type)
                    else " or ".join(t.__name__ for t in expected_type)
                )
                errors.append(f"Parameter '{key}' must be of type {type_names}")

        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

    @abstractmethod
    def _define_required_keys(self) -> dict:
        pass

    @abstractmethod
    def _validate_business_rules(self, parameters: dict):
        pass

    @abstractmethod
    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        pass


class PairwiseAlignmentStrategy(AnalysisExecutionStrategy):
    def _define_required_keys(self) -> dict:
        return {
            'sequence_a': str,
            'sequence_b': str,
            'mode': str,
            'match_score': (int, float),
            'mismatch_score': (int, float),
            'open_gap_score': (int, float),
            'extend_gap_score': (int, float)
        }
    
    def _validate_business_rules(self, parameters):
        return super()._validate_business_rules(parameters)

    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        parameters = analysis.parameters
        aligner = PairwiseAligner()

        aligner.mode = parameters['mode']
        aligner.match_score = parameters['match_score']
        aligner.mismatch_score = parameters['mismatch_score']
        aligner.open_gap_score = parameters['open_gap_score']
        aligner.extend_gap_score = parameters['extend_gap_score']

        alignments = aligner.align(parameters['sequence_a'], parameters['sequence_b'])

        results = []
        for aln in alignments:
            target = self._add_gaps(aln.target, aln.aligned[0])
            query = self._add_gaps(aln.query, aln.aligned[1])

            results.append({
                'score': aln.score,
                'query': query,
                'target': target,
            })

        command = PAIRWISE_ALIGNMENT_COMMAND_TEMPLATE.format(
            sequence_a=parameters['sequence_a'],
            sequence_b=parameters['sequence_b'],
            mode=parameters['mode'],
            match_score=parameters['match_score'],
            mismatch_score=parameters['mismatch_score'],
            open_gap_score=parameters['open_gap_score'],
            extend_gap_score=parameters['extend_gap_score'],
        )

        return AnalysisExecutionResult(
            command=command,
            result=results
        )

    def _add_gaps(self, seq, aligned):
        result = []
        last_end = 0
        for start, end in aligned:
            result.append('-' * (start - last_end))
            result.append(seq[start:end])
            last_end = end
        result.append('-' * (len(seq) - last_end))
        return ''.join(result)     
        

class HomologySearchStrategy(AnalysisExecutionStrategy):
    def _define_required_keys(self) -> dict:
        return {
            'database': (str),
            'type': (str),
            'sequences': (list),
            'evalue': (int, float),
            'gap_open': (int),
            'gap_extend': (int),
            'penalty': (int)
        }
    
    def _validate_business_rules(self, parameters: dict):
        if parameters['database'] not in BLAST_DB_PATHS.keys():
            raise ValueError('Invalid database specified')

        if parameters['penalty'] > 0:
            raise ValueError('Penalty must be negative')
    
    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        analysis.parameters['database'] = BLAST_DB_PATHS[analysis.parameters['database']]
        publisher = RabbitmqPublisher(exchange=BLASTN_EXCHANGE, routing_key=BLASTN_ROUTING_KEY)
        publisher.send_message({
            'analysis_id': analysis.id,
            'parameters': analysis.parameters,
            'type': analysis.type
        })
        return AnalysisExecutionResult(type=ExecutionType.ASYNC)