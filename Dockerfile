FROM python:3.9-slim-buster
LABEL maintainer="londonappdeveloper.com"

ENV PYTHONUNBUFFERED 1

COPY ./production.requirements.txt /requirements.txt
COPY ./app /app
COPY ./scripts /scripts
COPY ./build_commands /blast/build_commands

WORKDIR /app
EXPOSE 8000

RUN apt-get update && \
    apt-get install -y wget libgomp1 ncbi-blast+ && \
    mkdir -p /blast/taxonomy /blast/sequences /blast/db && \
    wget -P /blast/sequences https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Escherichia_coli/reference/GCF_000008865.2_ASM886v2/GCF_000008865.2_ASM886v2_genomic.fna.gz && \
    wget -P /blast/sequences https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Escherichia_coli/reference/GCF_000008865.2_ASM886v2/GCF_000008865.2_ASM886v2_genomic.gbff.gz && \
    gunzip /blast/sequences/GCF_000008865.2_ASM886v2_genomic.fna.gz && \
    gunzip /blast/sequences/GCF_000008865.2_ASM886v2_genomic.gbff.gz && \
    wget -P /blast/taxonomy https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz && \
    tar -xvzf /blast/taxonomy/taxdump.tar.gz -C /blast/taxonomy nodes.dmp names.dmp && \
    wget -P /blast/db https://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz && \
    tar -xvzf /blast/db/taxdb.tar.gz -C /blast/db && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apt-get install -y postgresql-client && \
    apt-get install -y --no-install-recommends \
        build-essential libpq-dev && \
    /py/bin/pip install -r /requirements.txt && \
    /py/bin/python3 /blast/build_commands/create_taxid_map.py -i /blast/sequences/GCF_000008865.2_ASM886v2_genomic.gbff -o /blast/taxonomy/taxid_map.txt && \
    makeblastdb -in /blast/sequences/GCF_000008865.2_ASM886v2_genomic.fna -dbtype nucl -parse_seqids -taxid_map /blast/taxonomy/taxid_map.txt -out /blast/db/escherichia_coli_db && \
    apt-get remove -y build-essential libpq-dev && \
    apt-get remove -y wget && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/scripts:/py/bin:$PATH"
ENV BLASTDB="/blast/db"

CMD ["run.sh"]
