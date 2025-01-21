import os
import shutil
import csv
from installed_clients.AssemblyUtilClient import AssemblyUtil


class KBaseAssemblyManager:
    def __init__(self, workspace_name, callback_url, token, scratch_dir, service_ver='release'):
        """
        Initializes the KBaseAssemblyManager with a workspace and AssemblyUtil client.

        :param workspace_name: Name of the KBase workspace.
        :param callback_url: Callback URL for the KBase service.
        :param token: Authentication token for KBase.
        :param scratch_dir: Path to the scratch directory for temporary file storage.
        :param service_ver: Version of the AssemblyUtil service (default: 'release').
        """
        self.workspace_name = workspace_name
        self.assembly_util = AssemblyUtil(callback_url, token=token, service_ver=service_ver)
        self.scratch_dir = scratch_dir
        self.assembly_mapping = {}

        # Ensure the scratch directory exists
        os.makedirs(self.scratch_dir, exist_ok=True)

    def save_assemblies_from_csv(self, csv_file_path):
        """
        Reads a CSV file, copies files to scratch, and saves assemblies in KBase.

        :param csv_file_path: Path to the input CSV file containing related genome data.
        """
        with open(csv_file_path, mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                related_genome_path = row['related_genome_path']
                related_name = row['related_name']
                if related_genome_path and related_name:
                    # Copy file to scratch directory
                    scratch_path = self.copy_to_scratch(related_genome_path)
                    
                    # Save the assembly
                    assembly_ref = self.save_assembly(scratch_path, related_name)
                    self.assembly_mapping[related_name] = assembly_ref

    def copy_to_scratch(self, file_path):
        """
        Copies a file to the scratch directory.

        :param file_path: Path to the file to be copied.
        :return: Path to the copied file in the scratch directory.
        """
        filename = os.path.basename(file_path)
        scratch_path = os.path.join(self.scratch_dir, filename)
        shutil.copy(file_path, scratch_path)
        return scratch_path

    def save_assembly(self, fasta_path, assembly_name):
        """
        Saves a single FASTA file as an assembly in the KBase workspace.

        :param fasta_path: Path to the FASTA file.
        :param assembly_name: Name to assign to the assembly in KBase.
        :return: Reference to the saved assembly.
        """
        assembly_ref = self.assembly_util.save_assembly_from_fasta2({
            'file': {'path': fasta_path},
            'workspace_name': self.workspace_name,
            'assembly_name': assembly_name
        })
        return assembly_ref

    def get_assembly_mapping(self):
        """
        Returns the dictionary of assembly names to their references.

        :return: Dictionary with assembly names as keys and references as values.
        """
        return self.assembly_mapping

    def print_assembly_mapping(self):
        """
        Prints the assembly mapping in a readable format.
        """
        objects_created = list()
        for assembly_name, assembly_info in self.assembly_mapping.items():
            objects_created.append({
                'ref':assembly_info['upa'], 
                'description': assembly_name})
       
        return objects_created
            #print(f"Assembly Name: {assembly_name}, Assembly Ref: {assembly_ref}")


# Example usage
if __name__ == "__main__":
    # Replace these with your workspace, callback URL, token, and scratch directory
    workspace_name = "your_workspace_name"
    callback_url = "your_callback_url"
    token = "your_token"
    scratch_dir = "/path/to/scratch"

    # Path to the input CSV file
    csv_file_path = "/path/to/related_genome_data.csv"

    # Initialize the manager
    manager = KBaseAssemblyManager(workspace_name, callback_url, token, scratch_dir)

    # Save assemblies from the CSV file
    manager.save_assemblies_from_csv(csv_file_path)

    # Print the assembly mapping
    manager.print_assembly_mapping()

