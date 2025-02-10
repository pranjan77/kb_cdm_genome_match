import os
import uuid
from installed_clients.WorkspaceClient import Workspace
import pandas as pd
import json

class GenomeSetProcessor:
    def __init__(self, token, ws_url):
        """
        Initialize the GenomeSetProcessor with a KBase token.

        Parameters:
            token (str): KBase authorization token.
        """
        self.ws = Workspace(ws_url, token=token)

    def fetch_genomeset_data(self, genomeset_ref):
        """
        Fetch genome data from a GenomeSet reference in KBase.

        Parameters:
            genomeset_ref (str): The reference to the GenomeSet object in KBase.

        Returns:
            list: List of dictionaries containing genome data.
        """
        # Fetch the GenomeSet object
        genomeset_object = self.ws.get_objects2({
            "objects": [{"ref": genomeset_ref}]
        })

        # Extract the genome elements
        genomeset_data = genomeset_object["data"][0]["data"]["elements"]

        # Parse the genome data into a list of dictionaries
        parsed_data_list = []
        for genome in genomeset_data:
            genome_ref = genomeset_data[genome]['ref']

            genome_name = self.ws.get_object_info3({
                "objects": [{"ref": genome_ref}]
            })['infos'][0][1]

            # Fetch the genome object using its ref
            genome_data = self.ws.get_objects2({
                "objects": [{"ref": genome_ref}]
            })["data"][0]["data"]

            parsed_data = {
                "genome_ref": genome_ref,
                "genome_name": genome_name,
                "taxonomy": genome_data.get("taxonomy", None),
                "gtdb_lineage": genome_data.get("std_lineages", {}).get("gtdb", {}).get("lineage", None),
                "gtdb_source_ver": genome_data.get("std_lineages", {}).get("gtdb", {}).get("source_ver", None),
                "gtdb_taxon_id": genome_data.get("std_lineages", {}).get("gtdb", {}).get("taxon_id", None),
                "taxon_assignment": genome_data.get("taxon_assignments", {}).get("GTDB_R08-RS214", None)
            }
            parsed_data_list.append(parsed_data)
        print (parsed_data_list)

        return parsed_data_list

    def generate_json(self, parsed_data_list, folder_path):
        """
        Generate a JSON representation of the genome data from a list of parsed data.

        Parameters:
            parsed_data_list (list): List of dictionaries containing genome data.
            folder_path (str): Path to the folder where the JSON file will be saved.

        Returns:
            str: Path to the JSON file.
        """
        os.makedirs(folder_path, exist_ok=True)

        json_file_path = os.path.join(folder_path, "genomeset_data.json")

        with open(json_file_path, "w") as file:
            json.dump(parsed_data_list, file, indent=4)  # Write JSON with indentation for readability


        return json_file_path
    

    def get_updated_genomeset_ref(self, genomeset_ref):
        """
        Given a genomeset_ref, calculate the new_genomeset_ref by incrementing its version.
        
        Args:
            ws (Workspace): KBase Workspace client instance.
            genomeset_ref (str): Reference to the genome set in the format "workspace_id/object_id/version".
            
        Returns:
            str: The new_genomeset_ref in the format "workspace_id/object_id/new_version".
        """


        # Get the genomeset name and find the latest genomeset_ref corresponding to that.
        # This is relevant when gtdb app has updated genomeset ref but the name remains same.

        # genomeset_info looks like the following
        # [19, 'Archaea_3.GenomeSet', 'KBaseSearch.GenomeSet-2.1', '2024-12-15T22:19:35+0000', 2, 
        # 'pranjan77', 75051, 'pranjan77:narrative_1734299479897', 'd471d10282fa184f5655ddc14abd541c',
        #  155, None]


        genomeset_info = self.ws.get_object_info3({
            "objects": [{"ref": genomeset_ref}]
        })['infos'][0]

        
        # Construct the genomeset reference from workspace_name/genomeset_name  
        ref = f"{genomeset_info[7]}/{genomeset_info[1]}"
        
    
        ginfo = self.ws.get_object_info3({
            "objects": [{"ref": ref}]
        })['infos'][0]
        
        # Construct the new genome set reference
        new_genomeset_ref = f"{ginfo[6]}/{ginfo[0]}/{ginfo[4]}"
        return new_genomeset_ref



    def generate_html(self, parsed_data_list, folder_path):
        """
        Generate an interactive HTML table from a list of parsed data.

        Parameters:
            parsed_data_list (list): List of dictionaries containing genome data.
            folder_path (str): Path to the folder where the HTML file will be saved.

        Returns:
            str: Path to the folder containing the HTML file.
        """
        # Create a DataFrame
        df = pd.DataFrame(parsed_data_list)

        # Convert the DataFrame to an HTML table
        table_html = df.to_html(index=False, classes='display', escape=False)

        # Add DataTables CDN, JavaScript, and CSS for max-width
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
            <script>
                $(document).ready(function() {{
                    $('#data_table').DataTable();
                }});
            </script>
            <style>
                /* Set maximum width for columns */
                td {{
                    max-width: 300px; /* Adjust as needed */
                    word-wrap: break-word;
                    white-space: normal;
                }}
                th {{
                    max-width: 300px; /* Adjust as needed */
                }}
            </style>
        </head>
        <body>
            <h1>Genome Taxonomy Information</h1>
            {table_html.replace('<table', '<table id="data_table"')}
        </body>
        </html>
        """

        os.makedirs(folder_path, exist_ok=True)

        # Save the HTML content to a file
        html_file_path = os.path.join(folder_path, "index.html")
        with open(html_file_path, "w") as file:
            file.write(html_content)

        return folder_path


"""
# Example usage
token = ""
ws_url = "https://appdev.kbase.us/services/ws"
processor = GenomeSetProcessor(token, ws_url)
genomeset_ref = "75051/19/2"
parsed_data = processor.fetch_genomeset_data(genomeset_ref)
folder = os.path.join(os.getcwd(), "output")
json_path = processor.generate_json(parsed_data, folder)
html_path = processor.generate_html(parsed_data, folder)
print(f"JSON file is saved at: {json_path}")
print(f"Interactive HTML file is saved in: {html_path}")
"""
