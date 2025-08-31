import os 

PAIRWISE_ALIGNMENT_COMMAND_TEMPLATE = '''from Bio.Align import PairwiseAligner
aligner = PairwiseAligner()
aligner.mode = "{mode}"
aligner.match_score = {match_score}
aligner.mismatch_score = {mismatch_score}
aligner.open_gap_score = {open_gap_score}
aligner.extend_gap_score = {extend_gap_score}
alignments = aligner.align("{sequence_a}", "{sequence_b}")
'''

BLAST_DB_PATHS = {
    'default': '/blast/db/environmental_bacteria_db'
}

BLASTN_EXCHANGE = os.environ.get('RABBITMQ_BLASTN_EXCHANGE_NAME')
BLASTN_ROUTING_KEY = os.environ.get('RABBITMQ_BLASTN_ROUTING_KEY')

RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER')
RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS')

AUTH_TOKEN_LIFETIME = int(os.environ.get('AUTH_TOKEN_LIFETIME', 30))