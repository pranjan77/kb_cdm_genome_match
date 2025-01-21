import json
import pandas as pd

from pathlib import Path

root = Path(__file__).parent  # This should be utils/

#merged_path = root / 'upa_taxonomy_kbase.tsv' 
merged_path = root / 'cdm_genome_expanded_taxonomy_path.tsv'

# Load the merged taxonomy file with genome information
merged_df = pd.read_csv(merged_path, sep='\t')

# Function to find closely related genomes within a specified range
def find_related_genomes(
    query_taxonomy, min_count=10, max_count=50, max_level='genus'
):
    # Parse the query taxonomy string into hierarchical levels
    query_levels = query_taxonomy.split(';')
    level_names = ['domain', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    
    # Ensure the max_level is valid and adjust the search range
    if max_level not in level_names:
        raise ValueError(f"Invalid max_level '{max_level}'. Must be one of {level_names}.")
    max_level_index = level_names.index(max_level)

    # Initialize an empty dictionary to store results
    results = {}

    # Traverse taxonomy levels from most specific to the max_level
    for i in range(len(level_names) - 1, max_level_index - 1, -1):
        # Create a filter for the current level
        level_filter = merged_df[level_names[:i + 1]] == query_levels[:i + 1]
        matches = merged_df[level_filter.all(axis=1)]
        
        # Add each match to the results with its match level
        for _, row in matches.iterrows():
            genome = row['genome']
            if genome not in results:  # Avoid overwriting entries from higher levels
                results[genome] = {
                    'taxonomy': row['taxonomy'],
                    'filepath': row['filepath'],
                    'match_level': level_names[i],
                }
        
        # Stop searching if we've reached the required number of genomes
        if len(results) >= min_count:
            break

    # Limit results to max_count
    limited_results = dict(list(results.items())[:max_count])

    # Determine the final level used to satisfy min_count
    final_level = results[next(iter(limited_results))]['match_level'] if limited_results else None

    return limited_results, final_level


def find_related_genomes_multiple(taxon_assignments, max_count, max_level):
    # Iterate over the taxon_assignment list to get related genomes
    output_results = []
    for taxon_assignment in taxon_assignments:
        # Find related genomes for the current taxonomy
        #TODO: Remove min_count and max_count
        related_genomes_dict, highest_level = find_related_genomes(
            taxon_assignment,  min_count=2, max_count=max_count, max_level=max_level
        )
        # Prepare the result dictionary for the current taxonomy
        result = {
            'taxon_assignment': taxon_assignment,
            'related_genomes': related_genomes_dict,
            'highest_level': highest_level
        }
        output_results.append(result)

    # Extract list of upas for for each taxon_assignment

    related_genome_upa_only_dict = {
        entry["taxon_assignment"]: [
           genome_info["filepath"]
           for genome_info in entry["related_genomes"].values()
        ]
        for entry in output_results
    }

    print ("===================output results=====================")
    print (output_results)

    print ("===================related_genomes_upda_only_dict=====================")

    print (related_genome_upa_only_dict)
    
    return (output_results, related_genome_upa_only_dict)

"""

# List of taxon_assignment strings (replace this with actual input)
taxon_assignments = [
    "d__Archaea;p__Halobacteriota;c__Methanosarcinia;o__Methanosarcinales;f__Methanosarcinaceae;g__Methanosarcina;s__Methanosarcina acetivorans",
    "d__Archaea;p__Halobacteriota;c__Archaeoglobi;o__Archaeoglobales;f__Archaeoglobaceae;g__Archaeoglobus;s__Archaeoglobus fulgidus"
]



for taxon_assignment in taxon_assignments:
    # Find related genomes for the current taxonomy
    related_genomes_dict, highest_level = find_related_genomes(
        taxon_assignment, merged_df, min_count=10, max_count=20, max_level='genus'
    )

   

# Save the results to a JSON file
output_json_path = "related_genomes_results.json"  # Replace with your desired output file path
with open(output_json_path, 'w') as json_file:
    json.dump(output_results, json_file, indent=4)

# Display the results (optional)
for result in output_results:
    print(json.dumps(result, indent=4))

"""
