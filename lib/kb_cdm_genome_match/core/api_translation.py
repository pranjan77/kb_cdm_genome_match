'''
Functions to translate values between the SDK API and core app logic.
'''

from typing import Dict, NamedTuple as _NamedTuple, cast as _cast


class GenomeCDMMatchParams(_NamedTuple):
    '''
    Parameters for running GTDB-tk in the KBase environment.
    '''

    ref: str
    ''' The workspace object reference in the x/y/z form. '''

    workspace_id: int
    ''' The ID of the KBase workspace where the report should be saved. '''

    output_tree_basename: str
    ''' The basename of the output KBase Tree objects. '''

    copy_proximals: int
    ''' Boolean copy proximal hit GTDB genome objects '''
    
    save_trees: int
    ''' Boolean save trees as objects and copy GTDB sp rep genomes in trees '''
    
    min_perc_aa: float
    ''' The mimimum sequence alignment in percent. '''

    db_ver: int
    ''' version of GTDB db, either 207 or 214 '''
    
    keep_intermediates: int
    ''' Boolean retain intermediate files in classify_wf '''
    
    overwrite_tax: int
    ''' Boolean overwrite an existing Taxonomy field in input Genome. '''

    dendrogram_report: int
    ''' Boolean use ultrametric tree in html report. '''


def get_cdm_genome_match_params(input_params: Dict[str, object]) -> GenomeCDMMatchParams:
    '''
    Process input parameters supplied to the GTDB-tk run method and parse them into
    a named tuple. The expected fields are:

    input_object_ref: a workspace reference to the input object that will be processed in the
        x/y/z form.
    workspace_id: the integer ID of the workspace where the results will be saved.
    min_perc_aa: the minimum sequence alignment as a percent.

    :param input_params: the input parameters passed to the method.
    :returns: the parsed parameters.
    :raises ValueError: if any of the parameters are invalid.
    '''
    wsid = input_params.get('workspace_id')
    if type(wsid) != int or _cast(int, wsid) < 1:
        raise ValueError('workspace_id is required and must be an integer > 0')

    ref = input_params.get('input_object_ref')
    if not ref:
        # for backwards compatibility
        ref = input_params.get('inputObjectRef')
    if type(ref) != str:
        raise ValueError('input_object_ref is required and must be a string')
    # could check ref format, but the ws will do that for us. YAGNI.

    output_tree_basename = input_params.get('output_tree_basename')
    if type(output_tree_basename) != str:
        raise ValueError('output_tree_basename is required and must be a string')

    copy_proximals = int(input_params.get('copy_proximals', 0))
    if type(copy_proximals) != int or (copy_proximals != 0 and copy_proximals != 1):
        raise ValueError('copy_proximals is required and must be an integer [0,1]')
    
    save_trees = int(input_params.get('save_trees', 0))
    if type(save_trees) != int or (save_trees != 0 and save_trees != 1):
        raise ValueError('save_trees is required and must be an integer [0,1]')
    
    min_perc_aa = input_params.get('min_perc_aa', 10)
    if type(min_perc_aa) != float and type(min_perc_aa) != int:
        raise ValueError('min_perc_aa must be a float')
    elif min_perc_aa < 0 or min_perc_aa > 100:
        raise ValueError('min_perc_aa must be a float [0,100]')

    db_ver = int(input_params.get('db_ver', 0))
    if type(db_ver) != int or (db_ver != 207 and db_ver != 214):
        raise ValueError('db_ver is required and must be an integer 207 or 214')
    
    keep_intermediates = int(input_params.get('keep_intermediates', 0))
    if type(keep_intermediates) != int or (keep_intermediates != 0 and keep_intermediates != 1):
        raise ValueError('keep_intermediates is required and must be an integer [0,1]')
    
    overwrite_tax = int(input_params.get('overwrite_tax', 0))
    if type(overwrite_tax) != int or (overwrite_tax != 0 and overwrite_tax != 1):
        raise ValueError('overwrite_tax is required and must be an integer [0,1]')

    dendrogram_report = int(input_params.get('dendrogram_report', 0))
    if type(dendrogram_report) != int or (dendrogram_report != 0 and dendrogram_report != 1):
        raise ValueError('dendrogram_report is required and must be an integer [0,1]')

    
    return GTDBTKParams(_cast(str, ref),
                        _cast(int, wsid),
                        _cast(str, output_tree_basename),
                        _cast(int, copy_proximals),
                        _cast(int, save_trees),
                        _cast(float, min_perc_aa) * 1.0,
                        _cast(int, db_ver),
                        _cast(int, keep_intermediates),
                        _cast(int, overwrite_tax),
                        _cast(int, dendrogram_report))
