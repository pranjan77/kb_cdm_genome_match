# Function to get list of genomes from a genomeset and return a list of genome uids
# use get_objects_2 to get the genomeset
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.WorkspaceClient import Workspace

import logging
logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)


def download_fasta_files(callback_url, ref_list):
    """
    Given a list of genome references (individual genomes or genomesets),
    downloads the corresponding fasta files for all genomes.
    
    Args:
        ref_list (list): A list containing genome_ref or genomeset_ref strings.
    
    Returns:
        dict: A mapping of genome_ref to the local file path of the downloaded fasta.
    """
    ref_fasta_path_dict = dict()
    assembly_util = AssemblyUtil(callback_url)
    ref_fasta_paths = assembly_util.get_fastas({'ref_lst':ref_list})
    for item in ref_fasta_paths:
        ref = item.split(";")[0]
        ref_fasta_path_dict[ref] = ref_fasta_paths[item]['paths'][0]
    return ref_fasta_path_dict



    
def append_metadata_to_object(object_ref, ws_url, workspace_name, ref_cdm_hits_metadata, provenance):
    # Initialize Workspace client
    ws = Workspace(ws_url)

    # Get the current object and its metadata
    get_objects_params = {
        'objects': [{'ref': object_ref}]    }
    result = ws.get_objects2(get_objects_params)


    # Define your provenance record
    provenance = [{
        "service": "kb_cdm_genome_match",
        "method": "run_mash_skani",
        "input_ws_objects": [object_ref]  # add any input object references if applicable
    }]

    # Extract the current object data and metadata
    object_data = result['data'][0]['data']
    current_metadata = result['data'][0]['info'][10]

    logging.info(ref_cdm_hits_metadata)
  
    # Append new metadata but ensuring the total metadata length is less than 850 characters
    total_metadata_len = 0
    new_metadata = dict()
    for item in ref_cdm_hits_metadata:
        #total_metadata_len += len(str(item))
        #logging.info(total_metadata_len)
        #if total_metadata_len < 850:
        if not new_metadata:
            new_metadata = item



    current_metadata.update({"cdm_best_hit":str(new_metadata)})

    # Prepare the object specification for saving
    save_object_params = {
        'objects': [{
            'type': result['data'][0]['info'][2],  # Use the original object type
            'data': object_data,
            'name': result['data'][0]['info'][1],  # Extract the object name from info
            'meta': current_metadata,
            'provenance': provenance
        }],
        'workspace': workspace_name  # Extract workspace ID from info
    }

    # Save the object with updated metadata
    try:
        ws.save_objects(save_object_params)
        return 1
    except Exception as e:
        print(f"Error appending metadata to object '{object_ref}': {e}")
        return 0
