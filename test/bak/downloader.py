"""
Download either a Genome or Assembly.
"""
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.AssemblyUtilClient import AssemblyUtil


def download_fasta(refs, cb_url):
    """
    Args:
      ref - workspace reference in the form 'workspace_id/object_id/obj_version'
      cb_url - callback server URL
    Returns the path of the downloaded fasta file
    """
    dfu = DataFileUtil(cb_url)
    assembly_util = AssemblyUtil(cb_url)
    ws_objects = dfu.get_objects({'object_refs': refs})
    paths = []
    for (obj, ref) in zip(ws_objects['data'], refs):
        ws_type = obj['info'][2]
        # This should be handled by AssemblyUtil, don't make the user do it
        if 'KBaseGenomes.Genome' in ws_type:
            assembly_ref = get_assembly_ref_from_genome(ref, obj)
        elif 'KBaseGenomeAnnotations.Assembly' in ws_type:
            assembly_ref = ref
        else:
            raise TypeError('Invalid type ' + ws_type + '. Must be an Assembly or Genome.')
        # Sooo what happens if the path for two different assemblies is the same?
        # AssemblyUtil seems to get a name from somewhere, and it's not a UUID or anything
        # that's guaranteed to be unique
        path = assembly_util.get_assembly_as_fasta({'ref': assembly_ref})['path']
        paths.append(path)
    return paths


def get_assembly_ref_from_genome(genome_ref, ws_obj):
    """
    Given a Genome object, fetch the reference to its Assembly object on the workspace.
    Arguments:
      ref is a workspace reference ID in the form 'workspace_id/object_id/version'
      ws_obj download workspace object for the genome
    Returns a workspace reference to an assembly object
    """
    # Extract out the assembly reference from the workspace data
    ws_data = ws_obj['data']
    assembly_ref = ws_data.get('contigset_ref') or ws_data.get('assembly_ref')
    if not assembly_ref:
        name = ws_obj['info'][1]
        raise TypeError('The Genome ' + name + ' has no assembly or contigset references')
    # Return a reference path of `genome_ref;assembly_ref`
    return genome_ref + ';' + assembly_ref
