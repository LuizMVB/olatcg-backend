# core/strategies.py
from __future__ import annotations

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Tuple, List

from django.db import transaction
from Bio.Blast import NCBIXML
from Bio.Align import PairwiseAligner

from .models import (
    Analysis,
    AnalysisTypeChoices,
    AnalysisStatusChoices,
    AnalysisInput,
    AnalysisOutput,
)
from .constants import (
    PAIRWISE_ALIGNMENT_COMMAND_TEMPLATE,
    BLAST_DB_PATHS,
    BLASTN_EXCHANGE,
    BLASTN_ROUTING_KEY,
)
from .rabbitmq_producer import RabbitmqPublisher

logger = logging.getLogger(__name__)


# ---------------- infra da Strategy (mantida) ----------------

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
        self._validate_business_rules(analysis.parameters)
        return self._perform_analysis(analysis)

    def _validate_parameters(self, parameters: dict, required_keys: dict):
        errors = []
        for key, expected_type in required_keys.items():
            if key not in parameters:
                errors.append(f"Missing required parameter: {key}")
                continue
            if not isinstance(parameters[key], expected_type):
                type_names = (
                    expected_type.__name__
                    if isinstance(expected_type, type)
                    else " or ".join(t.__name__ for t in expected_type)
                )
                errors.append(f"Parameter '{key}' must be of type {type_names}")
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

    @abstractmethod
    def _define_required_keys(self) -> dict: ...
    @abstractmethod
    def _validate_business_rules(self, parameters: dict): ...
    @abstractmethod
    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult: ...


# ---------------- Pairwise (como você já tinha) ----------------

class PairwiseAlignmentStrategy(AnalysisExecutionStrategy):
    def _define_required_keys(self) -> dict:
        return {
            'sequence_a': str,
            'sequence_b': str,
            'mode': str,
            'match_score': (int, float),
            'mismatch_score': (int, float),
            'open_gap_score': (int, float),
            'extend_gap_score': (int, float),
        }

    def _validate_business_rules(self, parameters):
        return

    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        p = analysis.parameters
        aligner = PairwiseAligner()
        aligner.mode = p['mode']
        aligner.match_score = p['match_score']
        aligner.mismatch_score = p['mismatch_score']
        aligner.open_gap_score = p['open_gap_score']
        aligner.extend_gap_score = p['extend_gap_score']

        alignments = aligner.align(p['sequence_a'], p['sequence_b'])
        results = []
        for aln in alignments:
            target = self._add_gaps(aln.target, aln.aligned[0])
            query = self._add_gaps(aln.query, aln.aligned[1])
            results.append({'score': aln.score, 'query': query, 'target': target})

        command = PAIRWISE_ALIGNMENT_COMMAND_TEMPLATE.format(
            sequence_a=p['sequence_a'],
            sequence_b=p['sequence_b'],
            mode=p['mode'],
            match_score=p['match_score'],
            mismatch_score=p['mismatch_score'],
            open_gap_score=p['open_gap_score'],
            extend_gap_score=p['extend_gap_score'],
        )
        return AnalysisExecutionResult(command=command, result=results)

    def _add_gaps(self, seq, aligned):
        result = []
        last_end = 0
        for start, end in aligned:
            result.append('-' * (start - last_end))
            result.append(seq[start:end])
            last_end = end
        result.append('-' * (len(seq) - last_end))
        return ''.join(result)


# ---------------- Homology Search (mantida) ----------------

class HomologySearchStrategy(AnalysisExecutionStrategy):
    def _define_required_keys(self) -> dict:
        return {
            'database': (str,),
            'type': (str,),
            'sequences': (list,),
            'evalue': (int, float),
            'gap_open': (int,),
            'gap_extend': (int,),
            'penalty': (int,),
        }

    def _validate_business_rules(self, parameters: dict):
        if parameters['database'] not in BLAST_DB_PATHS:
            raise ValueError('Invalid database specified')
        if parameters['penalty'] > 0:
            raise ValueError('Penalty must be negative')

    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        analysis.parameters['database'] = BLAST_DB_PATHS[analysis.parameters['database']]
        publisher = RabbitmqPublisher(exchange=BLASTN_EXCHANGE, routing_key=BLASTN_ROUTING_KEY)
        publisher.send_message({
            'analysis_id': analysis.id,
            'parameters': analysis.parameters,
            'type': analysis.type,
        })
        return AnalysisExecutionResult(type=ExecutionType.ASYNC)


# ---------------- Taxonomy Tree ----------------

class TaxonomyTreeStrategy(AnalysisExecutionStrategy):

    def __init__(self):
        super().__init__()
        self.parent_analysis: Optional[Analysis] = None

    def _define_required_keys(self) -> dict:
        return {'generated_from_analysis': (int,)}

    def _validate_business_rules(self, parameters: dict):
        parent_id = parameters['generated_from_analysis']
        parent = Analysis.objects.filter(pk=parent_id).first()

        if not parent:
            raise ValueError('Invalid "generated_from_analysis": parent analysis not found')
        if parent.type != AnalysisTypeChoices.HOMOLOGY_SEARCH:
            raise ValueError('Invalid "generated_from_analysis": parent must be HOMOLOGY_SEARCH')
        if parent.status != AnalysisStatusChoices.SUCCEEDED:
            raise ValueError('Parent analysis must be SUCCEEDED')
        
        self.parent_analysis = parent

    @transaction.atomic
    def _perform_analysis(self, analysis: Analysis) -> AnalysisExecutionResult:
        analysis.generated_from_analysis = self.parent_analysis
        analysis.save(update_fields=['generated_from_analysis'])

        # 1) Locate the fmt11 (.gz) file from the parent analysis (via generic AnalysisOutput)
        parent_out = (
            AnalysisOutput.objects
            .filter(input__analysis_id=self.parent_analysis.id)
            .order_by('-id')
            .first()
        )
        if not parent_out or not parent_out.file:
            raise ValueError('Homology output file (.gz) not found in parent analysis outputs')

        # 2) Storage directory for the current analysis (child)
        storage_dir = self._storage_dir(analysis.id)

        # 3) Decompress fmt11 .gz
        archive_path = self._decompress_to(storage_dir, parent_out.file, name='homology_archive', ext='fmt11')

        # 4) Convert fmt11 to XML using blast_formatter
        xml_tmp = self._tmp('.xml')
        self._run_blast_formatter_to_xml(archive_path, xml_tmp)
        xml_path = self._move_to_storage(xml_tmp, storage_dir, 'blast_output', 'xml')

        # 5) Parse XML and extract best hits
        records = self._parse_blast_xml(xml_path)
        best_hits = self._extract_best_hits(records)
        if not best_hits:
            raise ValueError('No best hits found in BLAST XML output')

        # 6) Generate FASTA file with best hits
        fasta_tmp = self._write_fasta(best_hits)
        fasta_path = self._move_to_storage(fasta_tmp, storage_dir, 'tree_muscle_input', 'fasta')

        # 7) Align sequences using MUSCLE
        aligned_tmp = self._tmp('.fasta')
        self._run_muscle(fasta_path, aligned_tmp)
        aligned_path = self._move_to_storage(aligned_tmp, storage_dir, 'tree_muscle_out', 'fasta')

        # 8) Generate phylogenetic tree using FastTree
        nwk_tmp = self._tmp('.nwk')
        self._run_fasttree(aligned_path, nwk_tmp)
        nwk_path = self._move_to_storage(nwk_tmp, storage_dir, 'tree', 'nwk')

        with open(nwk_path, 'r', encoding='utf-8') as fh:
            nwk_content = fh.read().strip()

        return AnalysisExecutionResult(
            command="blast_formatter | muscle | fasttree",
            result={'nwk': nwk_content},
            file=nwk_path,
            type=ExecutionType.SYNC,
        )

    # ---------- helpers ----------
    def _storage_dir(self, analysis_id: int) -> str:
        base = os.environ.get('STORAGE_FILE', '/mnt/data/blastn_storage')
        path = os.path.join(base, f'analysis_{analysis_id}')
        os.makedirs(path, exist_ok=True)
        return path

    def _tmp(self, suffix: str) -> str:
        return tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name

    def _move_to_storage(self, src: str, storage_dir: str, name: str, ext: str) -> str:
        dst = os.path.join(storage_dir, f"{name}.{ext}")
        shutil.move(src, dst)
        return dst

    def _decompress_to(self, storage_dir: str, gz_path: str, name: str, ext: str) -> str:
        tmp = self._tmp(f".{ext}")
        with gzip.open(gz_path, 'rb') as f_in, open(tmp, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        return self._move_to_storage(tmp, storage_dir, name, ext)

    def _run_blast_formatter_to_xml(self, archive_path: str, xml_out: str) -> None:
        cmd = ['blast_formatter', '-archive', archive_path, '-outfmt', '5', '-out', xml_out]
        logger.info("Running: %s", ' '.join(cmd))
        subprocess.run(cmd, check=True, text=True)

    def _parse_blast_xml(self, xml_path: str):
        with open(xml_path, 'r', encoding='utf-8') as handle:
            return list(NCBIXML.parse(handle))

    def _extract_best_hits(self, records) -> Dict[str, Tuple[str, str]]:
        best: Dict[str, Tuple[str, str]] = {}
        for rec in records:
            best_hsp = None
            best_alignment = None
            for aln in rec.alignments:
                for hsp in aln.hsps:
                    if best_hsp is None or hsp.score > best_hsp.score:
                        best_hsp = hsp
                        best_alignment = aln
            if best_hsp and best_alignment:
                best[rec.query] = (best_alignment.hit_id, best_hsp.sbjct)
        return best

    def _write_fasta(self, best_hits: Dict[str, Tuple[str, str]]) -> str:
        tmp = self._tmp('.fasta')
        with open(tmp, 'wb') as fh:
            for query_id, (_hit_id, seq) in best_hits.items():
                fh.write(f">{query_id}\n{seq}\n".encode())
        return tmp

    def _run_muscle(self, fasta_in: str, fasta_out: str) -> None:
        cmd = ['muscle', '-in', fasta_in, '-out', fasta_out]
        logger.info("Running: %s", ' '.join(cmd))
        subprocess.run(cmd, check=True, text=True)

    def _run_fasttree(self, aligned_fasta: str, nwk_out: str) -> None:
        cmd = ['fasttree', '-nt', aligned_fasta]
        logger.info("Running: %s > %s", ' '.join(cmd), nwk_out)
        with open(nwk_out, 'w', encoding='utf-8') as out:
            subprocess.run(cmd, check=True, text=True, stdout=out)