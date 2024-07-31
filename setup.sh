#!/bin/bash
set -ex

echo "Updating package lists"
apt-get update
echo "Installing dependencies"
apt-get install -y wget libgomp1 ncbi-blast+

echo "Creating directories"
mkdir -p /blast/taxonomy /blast/sequences /blast/db

echo "Downloading sequences"
wget -P /blast/sequences https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Agromyces_intestinalis/all_assembly_versions/GCF_008365295.1_ASM836529v1/GCF_008365295.1_ASM836529v1_genomic.fna.gz
gunzip /blast/sequences/GCF_008365295.1_ASM836529v1_genomic.fna.gz

wget -P /blast/sequences https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Agromyces_intestinalis/all_assembly_versions/GCF_008365295.1_ASM836529v1/GCF_008365295.1_ASM836529v1_genomic.gbff.gz
gunzip /blast/sequences/GCF_008365295.1_ASM836529v1_genomic.gbff.gz

echo "Downloading taxonomy data"
wget -P /blast/taxonomy https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -xvzf /blast/taxonomy/taxdump.tar.gz -C /blast/taxonomy nodes.dmp names.dmp

echo "Downloading BLAST database"
wget -P /blast/db https://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz
tar -xvzf /blast/db/taxdb.tar.gz -C /blast/db

echo "Setting up Python environment"
python -m venv /py
/py/bin/pip install --upgrade pip

echo "Installing PostgreSQL client and build essentials"
apt-get install -y postgresql-client
apt-get install -y --no-install-recommends build-essential libpq-dev
/py/bin/pip install -r /requirements.txt

echo "Creating taxid map"
/py/bin/python3 /build/create_taxid_map.py -i /blast/sequences/GCF_008365295.1_ASM836529v1_genomic.gbff -o /blast/taxonomy/taxid_map.txt

echo "Creating BLAST database"
makeblastdb -in /blast/sequences/GCF_008365295.1_ASM836529v1_genomic.fna -dbtype nucl -parse_seqids -taxid_map /blast/taxonomy/taxid_map.txt -out /blast/db/agromyces_intestinalis_db

echo "Cleaning up"
apt-get remove -y build-essential libpq-dev wget
rm -rf /var/lib/apt/lists/*
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Setup complete"
