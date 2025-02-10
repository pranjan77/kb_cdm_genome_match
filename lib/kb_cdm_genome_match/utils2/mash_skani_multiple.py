import subprocess
import pandas as pd
import os
import logging
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

def run_skani(query_fasta, reference_fasta_full_path, min_ani_threshold=95.0):
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
                return {
                    "query": query_filename,
                    "reference": os.path.basename(ref_genome_path),  # Extract only filename
                    "skani": skani_dist,
                    "ani": ani,
                    "shared_kmers": shared_kmers
                }

        except ValueError:
            logging.info(f"⚠️ Warning: Skipping invalid Skani result line - {line}")

    return None  

def mash_skani_pipeline(query_list, mash_db, taxonomy_file, top_n=10, max_mash_distance=0.05, min_ani_threshold=95.0, output_csv="mash_skani_results.csv"):
    """
    Runs Mash search, followed by Skani similarity search, and appends taxonomy data.
    Processes multiple query genomes.
    """
    taxonomy_dict = load_taxonomy_data(taxonomy_file)
    all_results = []

    for query_fasta in query_list:
        query_filename = os.path.basename(query_fasta)  # Extract query filename only
        logging.info(f"🔹 Running Mash search on {query_filename} against {mash_db}...")
        top_matches = run_mash_search(query_fasta, mash_db, top_n, max_mash_distance)

        for ref_genome_filename, mash_dist in top_matches:
            # Retrieve the full path for Skani
            ref_genome_full_path, taxonomy = taxonomy_dict.get(ref_genome_filename, (None, "Unknown"))
            
            if ref_genome_full_path is None:
                logging.info(f"⚠️ Warning: No full path found for {ref_genome_filename}. Skipping.")
                continue

            logging.info(f"🔹 Running Skani for {query_filename} vs {ref_genome_filename}...")
            skani_result = run_skani(query_fasta, ref_genome_full_path, min_ani_threshold)
            if skani_result:
                skani_result["query"] = query_filename  # Store query filename
                skani_result["mash_distance"] = mash_dist
                skani_result["taxonomy"] = taxonomy  # Match taxonomy
                all_results.append(skani_result)

    df = pd.DataFrame(all_results)
    df.to_csv(output_csv, index=False)
    logging.info(f"✅ Results saved to {output_csv}")

    return df


# Example Usage:
if __name__ == "__main__":
    query_genome1 = "/data/GTDB_v214/GCA/018/630/425/GCA_018630425.1_ASM1863042v1/GCA_018630425.1_ASM1863042v1_genomic.fna.gz"
    query_genome2 = "/data/GTDB_v214/GCA/018/263/505/GCA_018263505.1_ASM1826350v1/GCA_018263505.1_ASM1826350v1_genomic.fna.gz"
    mash_database = "/sketches/sketch_output/temp_sketches/combined_gtdb_sketch_410303_genome.msh"

    query_genomes = [query_genome1, query_genome2]  # List of multiple query FASTA files
    taxonomy_file = "/kb/module/genome_taxonomy_data/cdm_genomes_paths_taxonomy.tsv"  # Taxonomy file in tab-separated format
    top_results = 10
    max_mash_dist = 0.05
    min_ani = 95.0

    df_results = mash_skani_pipeline(query_genomes, mash_database, taxonomy_file, top_results, max_mash_dist, min_ani)
    print(df_results)

