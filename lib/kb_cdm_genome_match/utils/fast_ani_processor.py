
import os
import csv
import pandas as pd
import uuid

from .fast_ani_proc import run_fast_ani_pairwise
from .downloader import download_fasta

import hashlib

from pprint import pprint, pformat
import logging
logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)




def process_genomes(genomeset_taxonomy_data, related_genomes_only_dict, output_base_dir, callback_url):
    related_path_dict = dict()
    allpaths = list()
    for genome_data in genomeset_taxonomy_data:
        genome_ref = genome_data['genome_ref']
        taxonomy = genome_data['gtdb_lineage']

        logging.info("xxgenome_ref" + pformat(genomeset_taxonomy_data) )
        logging.info("xxrelated_genomes_only_dict" + pformat(related_genomes_only_dict) )


        if taxonomy not in related_genomes_only_dict:
            print(f"No related genomes found for taxonomy: {taxonomy}")
            continue

        related_refs = related_genomes_only_dict[taxonomy]

        # Create a separate output directory for this genome_ref
        output_directory = os.path.join(output_base_dir, genome_ref.replace("/", "_"))
        os.makedirs(output_directory, exist_ok=True)

        for related_ref_path in related_refs:
            # Ensure unique output for each pair
            unique_related_id = hashlib.sha256(related_ref_path.encode()).hexdigest() 
            related_path_dict[unique_related_id] = related_ref_path
            pair_output_dir = os.path.join(output_directory, str(unique_related_id))
            os.makedirs(pair_output_dir, exist_ok=True)
            print ([genome_ref, related_ref_path])


            genome_ref_path = download_fasta([genome_ref], callback_url)[0]
            paths = [genome_ref_path, related_ref_path]


            # Run Fast ANI for the pair
            #paths = download_fasta([genome_ref, related_ref], callback_url)
            print (paths)
            
            output_paths = run_fast_ani_pairwise(pair_output_dir, paths)
            logging.info("ouput_paths " + pformat(output_paths) )


            allpaths.append(output_paths)
            logging.info("allpaths " + pformat(allpaths) )


    return (allpaths, related_path_dict)


def get_taxonomy_all_refs (genomeset_taxonomy, related_genomes_only_dict):

    taxonomy_dict = dict()

    #Build taxonomy_dict
    for g in genomeset_taxonomy:
        genome_ref = g['genome_ref']
        gtdb_lineage = g['gtdb_lineage']
        taxonomy_dict[genome_ref] = gtdb_lineage

    for gtdb_lineage in related_genomes_only_dict:
        related_ref_paths = related_genomes_only_dict[gtdb_lineage]
        for related_ref_path in related_ref_paths:
            unique_related_id = hashlib.sha256(related_ref_path.encode()).hexdigest() 

            taxonomy_dict[unique_related_id] = gtdb_lineage

    return taxonomy_dict




def parse_and_write_fastani_output(file_lists, related_path_dict, taxonomy_dict, output_csv_path):
    """
    Parses FastANI output from a list of file pairs and writes the processed data to a CSV file.

    Args:
        file_lists (list): A list of file path pairs (tuples or lists of two file paths).
        output_csv_path (str): Path to the output CSV file.

    Returns:
        str: Path to the output CSV file.
    """
    parsed_data = []

    for file_pair in file_lists:
        file_path_1, file_path_2 = file_pair

        # Parse paths and extract information for the first file
        parts_1 = file_path_1.split("/")
        input_ref = parts_1[-3]
        related_ref = parts_1[-2]
        output_file_1 = parts_1[-1].strip()
        fastani_path1 = os.path.join("/".join(parts_1[:-1]), output_file_1)

        with open(fastani_path1, 'r') as f:
            fastani_details1 = f.read().strip().split()

        input_name = fastani_details1[0].split('/')[-1]
        related_name = fastani_details1[1].split('/')[-1]
        fastani_stats1 = ", ".join(fastani_details1[2:])


        pattern = "/kb/module/work/tmp/output_cdm_match/"
        fastani_path1_mod = fastani_path1.replace(pattern, "")
        alignment_path1 = f"{fastani_path1_mod}.visual"
        image_path1 = f"{alignment_path1}.pdf"

        # Parse paths and extract information for the second file
        parts_2 = file_path_2.split("/")
        output_file_2 = parts_2[-1].strip()
        fastani_path2 = os.path.join("/".join(parts_2[:-1]), output_file_2)

        with open(fastani_path2, 'r') as f:
            fastani_details2 = f.read().strip().split()

        fastani_stats2 = ", ".join(fastani_details2[2:])

        fastani_path2_mod = fastani_path2.replace(pattern, "")

        alignment_path2 = f"{fastani_path2_mod}.visual"
        image_path2 = f"{alignment_path2}.pdf"

        input_ref = input_ref.replace("_", "/")
        #related_ref = related_ref.replace("_", "/")
        related_genome_path = related_path_dict[related_ref]

        input_taxonomy = taxonomy_dict[input_ref]
        related_taxonomy = taxonomy_dict[related_ref]


        # Append parsed data for the current file pair
        parsed_data.append({
            'input_ref': input_ref,
            'input_name': input_name,
            'input_taxonomy': input_taxonomy,
            'related_genome_path': related_genome_path,

            'related_name': related_name,
            'related_taxonomy': related_taxonomy,

            'fastani_stat1': fastani_stats1,
            'fastani_stat2': fastani_stats2,
            'alignment_path1': alignment_path1,
            'image_path1': image_path1,
            'alignment_path2': alignment_path2,
            'image_path2': image_path2,
        })

    # Write parsed data to the output CSV
    fieldnames = ['input_ref', 'input_name', 'input_taxonomy',  'related_name', 'related_genome_path',
                  'related_taxonomy', 'fastani_stat1', 'fastani_stat2', 'alignment_path1', 
                  'image_path1', 'alignment_path2', 'image_path2']

    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parsed_data)

    return output_csv_path




def prepare_html(csv_path, html_path):
    """
    Converts a CSV file into an interactive HTML file with DataTables.

    Parameters:
        csv_path (str): Path to the input CSV file.
        html_path (str): Path to save the output HTML file.

    Returns:
        str: Path to the generated HTML file.
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Create hyperlinks for the last four columns
    df['alignment_image1'] = df['image_path1'].apply(lambda x: f'<a href="{x}" target="_blank">View Image 1</a>')
    df['alignment_details1'] = df['alignment_path1'].apply(lambda x: f'<a href="{x}" target="_blank">View Details 1</a>')
    df['alignment_image2'] = df['image_path2'].apply(lambda x: f'<a href="{x}" target="_blank">View Image 2</a>')
    df['alignment_details2'] = df['alignment_path2'].apply(lambda x: f'<a href="{x}" target="_blank">View Details 2</a>')

    # Drop the original columns
    df = df.drop(columns=['alignment_path1', 'image_path1', 'alignment_path2', 'image_path2'])

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

    # Save the HTML template to the specified file path
    with open(html_path, 'w') as f:
        f.write(html_content)

    return html_path



