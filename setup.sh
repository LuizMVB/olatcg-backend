set -ex

echo "Updating package lists"
apt-get update
echo "Installing dependencies"
apt-get install -y wget libgomp1 ncbi-blast+ fasttree muscle curl

#echo "Creating directories"
#mkdir -p /blast/taxonomy /blast/sequences /blast/db
#
#echo "Downloading sequences"
#echo "Downloading sequences"
## Bactérias de ambientes sadios (solo e água)
#wget -O /blast/sequences/Acinetobacter_johnsonii_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Acinetobacter_johnsonii/latest_assembly_versions/GCF_000162055.1_ASM16205v1/GCF_000162055.1_ASM16205v1_genomic.fna.gz
#wget -O /blast/sequences/Acinetobacter_johnsonii_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Acinetobacter_johnsonii/latest_assembly_versions/GCF_000162055.1_ASM16205v1/GCF_000162055.1_ASM16205v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Bacillus_cereus_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Bacillus_cereus_group_sp._BY10-2LC/latest_assembly_versions/GCF_027711705.1_ASM2771170v1/GCF_027711705.1_ASM2771170v1_genomic.fna.gz
#wget -O /blast/sequences/Bacillus_cereus_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Bacillus_cereus_group_sp._BY10-2LC/latest_assembly_versions/GCF_027711705.1_ASM2771170v1/GCF_027711705.1_ASM2771170v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Bacillus_sphaericus_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Lysinibacillus_sphaericus/latest_assembly_versions/GCF_000017965.1_ASM1796v1/GCF_000017965.1_ASM1796v1_genomic.fna.gz
#wget -O /blast/sequences/Bacillus_sphaericus_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Lysinibacillus_sphaericus/latest_assembly_versions/GCF_000017965.1_ASM1796v1/GCF_000017965.1_ASM1796v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Bacillus_thuringiensis_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Bacillus_thuringiensis/latest_assembly_versions/GCF_000008505.1_ASM850v1/GCF_000008505.1_ASM850v1_genomic.fna.gz
#wget -O /blast/sequences/Bacillus_thuringiensis_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Bacillus_thuringiensis/latest_assembly_versions/GCF_000008505.1_ASM850v1/GCF_000008505.1_ASM850v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Burkholderia_cepacia_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Burkholderia_cepacia/latest_assembly_versions/GCF_000292915.1_ASM29291v1/GCF_000292915.1_ASM29291v1_genomic.fna.gz
#wget -O /blast/sequences/Burkholderia_cepacia_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Burkholderia_cepacia/latest_assembly_versions/GCF_000292915.1_ASM29291v1/GCF_000292915.1_ASM29291v1_genomic.gbff.gz
#
## Bactérias do ciclo do nitrogênio
#wget -O /blast/sequences/Nitrobacter_sp_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrobacter_sp./latest_assembly_versions/GCF_017306235.1_ASM1730623v1/GCF_017306235.1_ASM1730623v1_genomic.fna.gz
#wget -O /blast/sequences/Nitrobacter_sp_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrobacter_sp./latest_assembly_versions/GCF_017306235.1_ASM1730623v1/GCF_017306235.1_ASM1730623v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Nitrobacter_winogradskyi_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrobacter_winogradskyi/latest_assembly_versions/GCF_000012725.1_ASM1272v1/GCF_000012725.1_ASM1272v1_genomic.fna.gz
#wget -O /blast/sequences/Nitrobacter_winogradskyi_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrobacter_winogradskyi/latest_assembly_versions/GCF_000012725.1_ASM1272v1/GCF_000012725.1_ASM1272v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Nitrosomonas_sp_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrosomonas_sp./latest_assembly_versions/GCF_003501205.1_ASM350120v1/GCF_003501205.1_ASM350120v1_genomic.fna.gz
#wget -O /blast/sequences/Nitrosomonas_sp_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrosomonas_sp./latest_assembly_versions/GCF_003501205.1_ASM350120v1/GCF_003501205.1_ASM350120v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Nitrosomonas_europaea_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrosomonas_europaea/latest_assembly_versions/GCF_000009145.1_ASM914v1/GCF_000009145.1_ASM914v1_genomic.fna.gz
#wget -O /blast/sequences/Nitrosomonas_europaea_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Nitrosomonas_europaea/latest_assembly_versions/GCF_000009145.1_ASM914v1/GCF_000009145.1_ASM914v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Rhizobium_leguminosarum_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Rhizobium_leguminosarum/latest_assembly_versions/GCF_000021345.1_ASM2134v1/GCF_000021345.1_ASM2134v1_genomic.fna.gz
#wget -O /blast/sequences/Rhizobium_leguminosarum_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Rhizobium_leguminosarum/latest_assembly_versions/GCF_000021345.1_ASM2134v1/GCF_000021345.1_ASM2134v1_genomic.gbff.gz
#
#wget -O /blast/sequences/Rhizobium_etli_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Rhizobium_etli/latest_assembly_versions/GCF_000092045.1_ASM9204v1/GCF_000092045.1_ASM9204v1_genomic.fna.gz
#wget -O /blast/sequences/Rhizobium_etli_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Rhizobium_etli/latest_assembly_versions/GCF_000092045.1_ASM9204v1/GCF_000092045.1_ASM9204v1_genomic.gbff.gz
#
## Cianobactérias
#wget -O /blast/sequences/Gloeobacter_violaceus_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Gloeobacter_violaceus/latest_assembly_versions/GCF_000011385.1_ASM1138v1/GCF_000011385.1_ASM1138v1_genomic.fna.gz
#wget -O /blast/sequences/Gloeobacter_violaceus_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Gloeobacter_violaceus/latest_assembly_versions/GCF_000011385.1_ASM1138v1/GCF_000011385.1_ASM1138v1_genomic.gbff.gz
#
#wget -O /blast/sequences/G_kilaueensis_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Gloeobacter_kilaueensis/latest_assembly_versions/GCF_000484535.1_ASM48453v1/GCF_000484535.1_ASM48453v1_genomic.fna.gz
#wget -O /blast/sequences/G_kilaueensis_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Gloeobacter_kilaueensis/latest_assembly_versions/GCF_000484535.1_ASM48453v1/GCF_000484535.1_ASM48453v1_genomic.gbff.gz
#
## Bactérias presentes em esgoto / Coliformes fecais
#wget -O /blast/sequences/Escherichia_coli_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz
#wget -O /blast/sequences/Escherichia_coli_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.gbff.gz
#
#wget -O /blast/sequences/Enterobacter_cloacae_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/905/331/265/GCF_905331265.2_AI2999v1_cpp/GCF_905331265.2_AI2999v1_cpp_genomic.fna.gz
#wget -O /blast/sequences/Enterobacter_cloacae_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/905/331/265/GCF_905331265.2_AI2999v1_cpp/GCF_905331265.2_AI2999v1_cpp_genomic.gbff.gz
#
#wget -O /blast/sequences/Klebsiella_pneumoniae_genomic.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/240/185/GCF_000240185.1_ASM24018v2/GCF_000240185.1_ASM24018v2_genomic.fna.gz
#wget -O /blast/sequences/Klebsiella_pneumoniae_genomic.gbff.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/240/185/GCF_000240185.1_ASM24018v2/GCF_000240185.1_ASM24018v2_genomic.gbff.gz
#
#
#echo "Downloading taxonomy data"
#wget -P /blast/taxonomy https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
#tar -xvzf /blast/taxonomy/taxdump.tar.gz -C /blast/taxonomy nodes.dmp names.dmp
#
#echo "Downloading BLAST database"
#wget -P /blast/db https://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz
#tar -xvzf /blast/db/taxdb.tar.gz -C /blast/db

echo "Setting up Python environment"
python -m venv /py
/py/bin/pip install --upgrade pip

echo "Installing PostgreSQL client and build essentials"
apt-get install -y postgresql-client
apt-get install -y --no-install-recommends build-essential libpq-dev
/py/bin/pip install -r /requirements.txt

#echo "Unzip /sequences/*"
#gunzip /blast/sequences/*.gz
#
## Criar o mapa de taxid a partir de todos os arquivos .gbff
#echo "Creating taxid map"
#find /blast/sequences -name "*.gbff" | while read gbff_file; do
#    /py/bin/python3 /build/create_taxid_map.py -i "$gbff_file" -o /blast/taxonomy/taxid_map.txt --append
#done

## Criar o banco de dados BLAST a partir de todos os arquivos .fna
#echo "Creating BLAST database"
#cat /blast/sequences/*.fna > /blast/sequences/combined_sequences.fna
#makeblastdb -in /blast/sequences/combined_sequences.fna -dbtype nucl -parse_seqids -taxid_map /blast/taxonomy/taxid_map.txt -out /blast/db/environmental_bacteria_db

echo "Cleaning up"
apt-get remove -y build-essential libpq-dev wget
rm -rf /var/lib/apt/lists/*
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Setup complete"