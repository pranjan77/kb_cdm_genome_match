import subprocess
import pandas as pd

def run_mash_search(query_fasta, mash_db, top_n=10, max_mash_distance=0.05):
    """
    Runs Mash search to find the closest matches for a given query genome.
    Filters results based on Mash distance.
    
    :param query_fasta: Path to the query genome FASTA file.
    :param mash_db: Path to the Mash database (.msh file).
    :param top_n: Number of top matches to return.
    :param max_mash_distance: Maximum Mash distance allowed.
    :return: List of top matching genome paths.
    """
    mash_cmd = f"mash dist {mash_db} {query_fasta}"
    result = subprocess.run(mash_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error running Mash: {result.stderr}")

    # Parse Mash results
    mash_results = []
    for line in result.stdout.strip().split("\n"):
        fields = line.split("\t")
        if len(fields) >= 3:
            genome, _, distance, *_ = fields
            distance = float(distance)
            if distance <= max_mash_distance:  # Apply Mash distance filter
                mash_results.append((genome, distance))

    # Sort results by Mash distance and select top N
    mash_results.sort(key=lambda x: x[1])
    top_matches = [genome for genome, _ in mash_results[:top_n]]

    return top_matches


def run_skani(query_fasta, reference_fasta, min_ani_threshold=95.0):
    """
    Runs Skani similarity search between a query genome and a reference genome.
    Filters results based on ANI threshold.
    
    :param query_fasta: Path to the query genome FASTA file.
    :param reference_fasta: Path to the reference genome FASTA file.
    :param min_ani_threshold: Minimum ANI required to include result.
    :return: Dictionary with Skani similarity results if it meets the threshold.
    """
    skani_cmd = f"skani dist {query_fasta} {reference_fasta}"
    result = subprocess.run(skani_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error running Skani: {result.stderr}")

    # Parse Skani results
    for line in result.stdout.strip().split("\n"):
        fields = line.split("\t")
        if len(fields) >= 4:
            ref_genome, skani_dist, ani, shared_kmers = fields[:4]
            ani = float(ani)
            if ani >= min_ani_threshold:  # Apply ANI threshold filter
                return {
                    "reference": ref_genome,
                    "skani_distance": float(skani_dist),
                    "ani": ani,
                    "shared_kmers": shared_kmers
                }

    return None


def mash_skani_pipeline(query_fasta, mash_db, top_n=10, max_mash_distance=0.05, min_ani_threshold=95.0, output_csv="mash_skani_results.csv"):
    """
    Runs Mash search to find top matches and then Skani to refine similarity scores.
    Applies filtering based on Mash distance and ANI threshold.
    
    :param query_fasta: Path to the query genome FASTA file.
    :param mash_db: Path to the Mash database (.msh file).
    :param top_n: Number of top matches to process with Skani.
    :param max_mash_distance: Maximum Mash distance allowed.
    :param min_ani_threshold: Minimum ANI required for Skani results.
    :param output_csv: Path to save the final results.
    :return: DataFrame with results.
    """
    print(f"Running Mash search on {query_fasta} against {mash_db} with max Mash distance {max_mash_distance}...")
    top_matches = run_mash_search(query_fasta, mash_db, top_n, max_mash_distance)

    results = []
    for ref_genome in top_matches:
        print(f"Running Skani similarity for {query_fasta} vs {ref_genome} with min ANI {min_ani_threshold}...")
        skani_result = run_skani(query_fasta, ref_genome, min_ani_threshold)
        if skani_result:
            results.append(skani_result)

    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

    return df


# Example Usage:
if __name__ == "__main__":
    query_genome = "query.fasta"
    mash_database = "gtdb_sketch.msh"
    top_results = 10
    max_mash_dist = 0.05  # Only consider genomes with Mash distance ≤ 0.05
    min_ani = 95.0  # Only consider genomes with ANI ≥ 95%

    df_results = mash_skani_pipeline(query_genome, mash_database, top_results, max_mash_dist, min_ani)
    print(df_results)

