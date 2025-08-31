set -ex

echo "Updating package lists"
apt-get update

echo "Installing dependencies"
# troque 'muscle' por 'muscle3' (v3.x com -in/-out)
apt-get install -y wget libgomp1 ncbi-blast+ fasttree muscle3 curl

# opcional: manter o nome 'muscle' apontando para o binário do muscle3
ln -sf /usr/bin/muscle3 /usr/local/bin/muscle

echo "Setting up Python environment"
python -m venv /py
/py/bin/pip install --upgrade pip

echo "Installing PostgreSQL client and build essentials"
apt-get install -y postgresql-client
apt-get install -y --no-install-recommends build-essential libpq-dev
/py/bin/pip install -r /requirements.txt

echo "Cleaning up"
apt-get remove -y build-essential libpq-dev wget
rm -rf /var/lib/apt/lists/*
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Setup complete"