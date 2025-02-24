import subprocess
import pandas as pd
import os
import logging

from  .calculate_hash import read_fasta2, contig_set_hash
from .KBaseObjectUtils import append_metadata_to_object

logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)


def load_taxonomy_data(taxonomy_file):
    """
    Reads the taxonomy file and returns a dictionary mapping filepaths to taxonomy strings.
    """
    taxonomy_df = pd.read_csv(taxonomy_file, sep="\t")
    # Store full paths for lookup instead of just filenames
    taxonomy_dict = {os.path.basename(filepath): (filepath, taxonomy) for filepath, taxonomy in zip(taxonomy_df['filepath'], taxonomy_df['taxonomy'])}
    return taxonomy_dict

def run_mash_search(query_fasta, mash_db, top_n=10, max_mash_distance=0.05):
    """
    Runs Mash search to find the closest matches for a given query genome.
    Filters results based on Mash distance.
    """
    mash_cmd = f"mash dist {mash_db} {query_fasta}"
    result = subprocess.run(mash_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error running Mash: {result.stderr}")

    mash_results = []
    for line in result.stdout.strip().split("\n"):
        fields = line.split("\t")
        if len(fields) >= 3:
            genome_path, _, distance, *_ = fields
            distance = float(distance)
            genome_filename = os.path.basename(genome_path)  # Extract only filename
            if distance <= max_mash_distance:
                mash_results.append((genome_filename, distance))

    mash_results.sort(key=lambda x: x[1])
    top_matches = mash_results[:top_n]
    return top_matches  

def run_skani(ref,query_fasta, reference_fasta_full_path, min_ani_threshold=95.0):
    """
    Runs Skani similarity search between a query genome and a reference genome.
    Filters results based on ANI threshold.
    """
    skani_cmd = f"skani dist {query_fasta} {reference_fasta_full_path}"
    result = subprocess.run(skani_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        logging.info(f"⚠️ Warning: Skipping {reference_fasta_full_path} due to Skani error: {result.stderr}")
        return None

    for line in result.stdout.strip().split("\n"):
        fields = line.split("\t")

        if len(fields) < 5 or fields[2] == "ANI":
            continue

        try:
            ref_genome_path = fields[0]
            skani_dist = float(fields[2])
            ani = float(fields[3])
            shared_kmers = fields[4]

            query_filename = os.path.basename(query_fasta)  # Extract query filename only
            if ani >= min_ani_threshold:
                contigs = read_fasta2(ref_genome_path)
                cdm_hash = contig_set_hash(contigs)
                return {
                    "input_ref": ref,
                    "query": query_filename,
                    "cdm_hash":cdm_hash,
                    "reference": os.path.basename(ref_genome_path),  # Extract only filename
                    "skani": skani_dist,
                    "ani": ani,
                    "shared_kmers": shared_kmers
                }

        except ValueError:
            logging.info(f"⚠️ Warning: Skipping invalid Skani result line - {line}")

    return None  

def mash_skani_pipeline(ref_fasta_path_dict, mash_db, taxonomy_file, ws_url, workspace_name, provenance, top_n=10, 
                        max_mash_distance=0.05, min_ani_threshold=95.0, 
                        output_csv="mash_skani_results.csv"):
    """
    Runs Mash search, followed by Skani similarity search, and appends taxonomy data.
    Processes multiple query genomes.
    

    """

    taxonomy_dict = load_taxonomy_data(taxonomy_file)
    all_results = []

    for ref in ref_fasta_path_dict:
        query_fasta = ref_fasta_path_dict[ref]
        query_filename = os.path.basename(query_fasta)  # Extract query filename only
        logging.info(f"🔹 Running Mash search on {query_filename} against {mash_db}...")
        top_matches = run_mash_search(query_fasta, mash_db, top_n, max_mash_distance)

        ref_cdm_hits_metadata = list()
        count_hits = 0
        for ref_genome_filename, mash_dist in top_matches:
            # Retrieve the full path for Skani
            ref_genome_full_path, taxonomy = taxonomy_dict.get(ref_genome_filename, (None, "Unknown"))
            
            if ref_genome_full_path is None:
                logging.info(f"⚠️ Warning: No full path found for {ref_genome_filename}. Skipping.")
                continue

            logging.info(f"🔹 Running Skani for {query_filename} vs {ref_genome_filename}...")
            skani_result = run_skani(ref,query_fasta, ref_genome_full_path, min_ani_threshold)
            if skani_result:
                count_hits += 1
                ref_cdm_hits_metadata.append({"cdm_hash":skani_result["cdm_hash"], "skani":skani_result['skani'],
                                              "ani":skani_result['ani'], "shared_kmers":skani_result['shared_kmers'],
                                              "name":ref_genome_filename
                                              })
                skani_result["query"] = query_filename  # Store query filename
                skani_result["mash_distance"] = mash_dist
                skani_result["taxonomy"] = taxonomy  # Match taxonomy
                all_results.append(skani_result)
        if count_hits == 0:
            skani_result = {"input_ref":ref,
                           "query":query_filename}
            all_results.append(skani_result)
        logging.info(f" =========Now appending Metadata appended to {ref}===============")
        append_metadata_to_object(ref, ws_url, workspace_name, ref_cdm_hits_metadata,  provenance)
    
    df = pd.DataFrame(all_results)
    df.fillna("", inplace=True)
    df.to_csv(output_csv, index=False)
    logging.info(f"Results saved to {output_csv}")

    return df

