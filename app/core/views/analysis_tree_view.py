import gzip
import shutil
import os
import tempfile
import subprocess
from Bio.Blast import NCBIXML
from django.db import transaction
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Analysis, AnalysisTypeChoices, AnalysisStatusChoices, MuscleInput, MuscleOutput, FastTreeInput, \
    FastTreeOutput, BlastnInput, BlastnOutput
from core.serializers import AnalysisTreeSerializer, FastTreeOutputSerializer


class AnalysisTreeView(APIView):

    def get_storage_directory(self, analysis_id):
        """Creates a directory for storing the files related to the tree analysis."""
        storage_dir = os.path.join(os.environ.get('STORAGE_FILE', '/mnt/data/blastn_storage'), f'analysis_{analysis_id}')
        os.makedirs(storage_dir, exist_ok=True)
        return storage_dir

    def store_file(self, source_path, analysis_id, file_type, file_extension):
        """Moves the file from temp to the storage directory."""
        storage_dir = self.get_storage_directory(analysis_id)
        stored_file_path = os.path.join(storage_dir, f"{file_type}.{file_extension}")
        shutil.move(source_path, stored_file_path)
        return stored_file_path

    def format_blast_output_to_xml(self, decompressed_file_path, analysis_id):
        """Formats the BLAST output to XML (outfmt 5) using the blast_formatter command."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as formatted_output_file:
            formatted_output_path = formatted_output_file.name

        blast_formatter_command = [
            'blast_formatter',
            '-archive', decompressed_file_path,  # Use the decompressed file path here
            '-outfmt', '5',  # XML format
            '-out', formatted_output_file.name
        ]

        formatter_result = subprocess.run(blast_formatter_command, text=True)

        if formatter_result.returncode != 0:
            raise subprocess.CalledProcessError(formatter_result.returncode, blast_formatter_command)

        # Move the XML file to the storage directory
        xml_file_path = self.store_file(formatted_output_path, analysis_id, 'blast_output', 'xml')

        return xml_file_path

    def parse_blast_xml(self, xml_file_path):
        with open(xml_file_path) as result_handle:
            blast_records = NCBIXML.parse(result_handle)
            return list(blast_records)

    def extract_best_hits(self, blast_records):
        best_hits = {}
        for record in blast_records:
            best_hsp = None
            for alignment in record.alignments:
                for hsp in alignment.hsps:
                    if best_hsp is None or hsp.score > best_hsp.score:
                        best_hsp = hsp
                        best_hits[record.query] = alignment.hit_id, hsp.sbjct
        return best_hits

    def create_fasta_from_best_hits(self, best_hits, analysis_id):
        """Create a FASTA file with the best hits and store it."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as fasta_file:
            for query_id, (hit_id, sequence) in best_hits.items():
                fasta_file.write(f">{query_id}\n{sequence}\n".encode())

        # Move the generated FASTA file to storage
        fasta_file_path = self.store_file(fasta_file.name, analysis_id, 'tree_muscle_input', 'fasta')

        return fasta_file_path

    def run_muscle(self, fasta_file_path, analysis_id):
        """Executes the muscle CLI and saves the aligned sequence."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as aligned_fasta_file:
            muscle_command = [
                'muscle',
                '-in', fasta_file_path,
                '-out', aligned_fasta_file.name
            ]

            result = subprocess.run(muscle_command, text=True)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, muscle_command)

        # Move the aligned FASTA file to storage
        aligned_fasta_file_path = self.store_file(aligned_fasta_file.name, analysis_id, 'tree_muscle_out', 'fasta')

        return aligned_fasta_file_path

    def run_fasttree(self, aligned_fasta_file_path, analysis_id):
        """Executes the fasttree CLI and saves the Newick tree."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nwk') as nwk_file:
            fasttree_command = [
                'fasttree',
                '-nt', aligned_fasta_file_path
            ]

            result = subprocess.run(fasttree_command, text=True, stdout=nwk_file)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, fasttree_command)

        # Move the Newick file to storage
        nwk_file_path = self.store_file(nwk_file.name, analysis_id, 'tree', 'nwk')

        return nwk_file_path

    def create_phylogenetic_tree_analysis(self, from_analysis, fasta_file_path, aligned_fasta_file_path, nwk_file_path, title, description):
        """Persists the phylogenetic tree analysis with input/output file paths."""
        phylo_tree_analysis = Analysis.objects.create(
            title=title,
            description=description,
            type=AnalysisTypeChoices.TAXONOMY_TREE,
            status=AnalysisStatusChoices.EXECUTION_SUCCEEDED,
            generated_from_analysis=from_analysis,
            experiment=from_analysis.experiment,
        )

        # Save MuscleInput
        muscle_input = MuscleInput.objects.create(
            analysis=phylo_tree_analysis,
            input_file=fasta_file_path  # Store the file path
        )

        # Save MuscleOutput
        MuscleOutput.objects.create(
            input=muscle_input,
            output_file=aligned_fasta_file_path  # Store the aligned file path
        )

        # Save FastTreeInput
        fasttree_input = FastTreeInput.objects.create(
            analysis=phylo_tree_analysis,
            input_file=aligned_fasta_file_path  # Store the aligned file path
        )

        # Save FastTreeOutput
        FastTreeOutput.objects.create(
            input=fasttree_input,
            output_file=nwk_file_path  # Store the tree file path
        )

        return phylo_tree_analysis

    def decompress_file(self, compressed_file_path, analysis_id):
        """Decompresses a .gz file and returns the path to the uncompressed file."""
        decompressed_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.fasta').name
        with gzip.open(compressed_file_path, 'rb') as f_in, open(decompressed_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"Decompressed file: {decompressed_file_path}")
        return self.store_file(decompressed_file_path, analysis_id, 'decompressed', 'fasta')

    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        try:
            # Retrieve the analysis object
            analysis = Analysis.objects.get(pk=analysis_id)
        except Analysis.DoesNotExist:
            raise serializers.ValidationError('Analysis not found: try another id')

        if analysis.type != 'HOMOLOGY':
            raise serializers.ValidationError('Analysis type is not "HOMOLOGY"; Taxonomy Tree can only be generated from "HOMOLOGY" analysis')

        try:
            analysis_generated_from_this = Analysis.objects.get(generated_from_analysis=analysis_id)

            if analysis_generated_from_this is not None:
                fasttree_outputs = FastTreeOutput.objects.filter(input__analysis=analysis_generated_from_this).all()
                nwk_file_path = fasttree_outputs[0].output_file
                with open(nwk_file_path, 'r') as nwk_file:
                    nwk_content = nwk_file.read().strip()
                    return Response(data={'nwk': nwk_content, 'analysis_id': analysis_generated_from_this.id})
        except Analysis.DoesNotExist:
            pass

        # Deserialize the request data
        serializer = AnalysisTreeSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        try:
            # Get Blastn input and output files for the analysis
            blastn_input = BlastnInput.objects.get(analysis_id=analysis_id)
            homology_output = BlastnOutput.objects.get(input=blastn_input)
        except BlastnInput.DoesNotExist:
            raise serializers.ValidationError('BlastnInput not found for the given analysis id')
        except BlastnOutput.DoesNotExist:
            raise serializers.ValidationError('BlastnOutput not found for the given BlastnInput')

        # Step 1: Decompress the BLAST output file
        output_file_path = homology_output.output_file
        output_file_decompressed = self.decompress_file(output_file_path, analysis_id)

        # Step 2: Convert BLAST output to XML format
        xml_file_path = self.format_blast_output_to_xml(output_file_decompressed, analysis_id)

        # Step 3: Parse BLAST XML output and extract best hits
        blast_records = self.parse_blast_xml(xml_file_path)
        best_hits = self.extract_best_hits(blast_records)

        # Step 4: Create a FASTA file from the best hits
        fasta_file_path = self.create_fasta_from_best_hits(best_hits, analysis_id)

        # Step 5: Run MUSCLE to align sequences
        aligned_fasta_file_path = self.run_muscle(fasta_file_path, analysis_id)

        # Step 6: Run FastTree to generate a phylogenetic tree
        nwk_file_path = self.run_fasttree(aligned_fasta_file_path, analysis_id)

        # Step 7: Persist the new analysis data
        new_analysis = self.create_phylogenetic_tree_analysis(
            analysis,
            fasta_file_path,
            aligned_fasta_file_path,
            nwk_file_path,
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description']
        )

        with open(nwk_file_path, 'r') as nwk_file:
            nwk_content = nwk_file.read().strip()  # Remove any trailing newline characters
            return Response(data={'nwk': nwk_content, 'analysis_id': new_analysis.id})

