import argparse
from Bio import SeqIO

def parse_genbank(genbankfile, output_file):
    with open(output_file, 'w') as f:
        for gb in SeqIO.parse(genbankfile, "genbank"):
            try:
                # Extract sequence ID
                annotations = gb.id

                # Extract taxonomic ID from the first feature's db_xref
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
                print(f"An error occurred: {e}")
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse GenBank file to extract taxonomic IDs.')
    parser.add_argument('-i', '--input', required=True, help='Input GenBank flat file format (gbff) file')
    parser.add_argument('-o', '--output', required=True, help='Output taxid_map file')
    
    args = parser.parse_args()
    parse_genbank(args.input, args.output)
