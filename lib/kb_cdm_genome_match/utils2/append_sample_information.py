import pandas as pd
import logging
logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

def merge_mash_skani_with_sample(mash_skani_file, genome_sample_file, output_file="merged_results.csv"):
    """
    Merges Mash-Skani results with genome sample metadata using the reference genome.

    :param mash_skani_file: Path to mash_skani_results.csv
    :param genome_sample_file: Path to genome_sample.csv
    :param output_file: Path to save merged results (default: "merged_results.csv")
    :return: Merged DataFrame
    """
    # Load the Mash-Skani results
    mash_skani_df = pd.read_csv(mash_skani_file)
    if 'reference' not in mash_skani_df.columns:
    # Create a reference column based on the index (or another logic)
         mash_skani_df['reference'] = mash_skani_df.index.astype(str)


    logging.info("Mash-Skani results loaded")

    logging.info(mash_skani_df)

    # Load the genome sample metadata
    genome_sample_df = pd.read_csv(genome_sample_file)

    # Ensure the reference column and Accession column are properly formatted
    #mash_skani_df['reference'] = mash_skani_df['reference']
    #genome_sample_df['Accession'] = genome_sample_df['Accession'].str.strip()

    # Merge both dataframes based on reference == Accession
    merged_df = mash_skani_df.merge(genome_sample_df, left_on="reference", right_on="Accession", how="left")

    # Drop the duplicated Accession column (since it's the same as reference)
    merged_df.drop(columns=["Accession"], inplace=True)
    merged_df.fillna("", inplace=True)


    # Save the merged output
    merged_df.to_csv(output_file, index=False)

    logging.info(f"✅ Merged file saved as {output_file}")

    return merged_df

# Example Usage:
if __name__ == "__main__":
    merged_df = merge_mash_skani_with_sample("mash_skani_results.csv", "genome_sample.csv")
    print(merged_df.head())  # Display the first few rows
