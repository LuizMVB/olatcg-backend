import argparse
from Bio import SeqIO

def parse_genbank(genbankfile, output_file, append):
    # Definir o modo de abertura do arquivo: 'a' para append, 'w' para sobrescrever
    mode = 'a' if append else 'w'

    with open(output_file, mode) as f:
        for gb in SeqIO.parse(genbankfile, "genbank"):
            try:
                # Extrair o ID da sequência
                annotations = gb.id

                # Extrair o ID taxonômico da primeira feature's db_xref
                for feature in gb.features:
                    if 'db_xref' in feature.qualifiers:
                        for db_xref in feature.qualifiers['db_xref']:
                            if db_xref.startswith('taxon:'):
                                taxid = db_xref.split(':')[1]
                                f.write("{} {}\n".format(annotations, taxid))
                                break
                    if 'taxid' in locals():
                        break
            except Exception as e:
                print(f"An error occurred while processing {genbankfile}: {e}")
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse GenBank file to extract taxonomic IDs.')
    parser.add_argument('-i', '--input', required=True, help='Input GenBank flat file format (.gbff) file')
    parser.add_argument('-o', '--output', required=True, help='Output taxid_map file')
    parser.add_argument('--append', action='store_true', help='Append to the output file instead of overwriting')

    args = parser.parse_args()
    parse_genbank(args.input, args.output, args.append)
