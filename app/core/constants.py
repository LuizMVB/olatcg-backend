import os

TAX_ID_FILE = '/blast/taxonomy/taxid_map.txt'
NODES_FILE = '/blast/taxonomy/nodes.dmp'
NAMES_FILE = '/blast/taxonomy/names.dmp'
BLAST_DB_PATHS = {
    'default': '/blast/db/environmental_bacteria_db'
}

BLASTN_EXCHANGE = os.environ.get('RABBITMQ_BLASTN_EXCHANGE_NAME')
BLASTN_ROUTING_KEY = os.environ.get('RABBITMQ_BLASTN_ROUTING_KEY')
