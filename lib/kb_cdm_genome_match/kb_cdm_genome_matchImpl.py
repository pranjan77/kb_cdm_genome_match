# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import logging
import os
import sys
import subprocess
from datetime import datetime
from pprint import pprint, pformat
from pathlib import Path



from kb_cdm_genome_match.core.api_translation import get_cdm_genome_match_params
from kb_cdm_genome_match.core.html_report_creator import HTMLReportCreator
from kb_cdm_genome_match.core.genomeset_processor import GenomeSetProcessor
from kb_cdm_genome_match.core.kb_client_set import KBClients
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.kb_gtdbtkClient import kb_gtdbtk

from .utils.fast_ani_proc import run_fast_ani_pairwise
from .utils.fast_ani_output import get_result_data
from .utils.downloader import download_fasta
from .utils.fast_ani_report import create_report

from installed_clients.WorkspaceClient import Workspace


#END_HEADER


class kb_cdm_genome_match:
    '''
    Module Name:
    kb_cdm_genome_match
    Module Description:
    
    '''
    
    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################

    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""
    
    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block

    def now_ISOish(self):
        now_timestamp = datetime.now()
        now_secs_from_epoch = (now_timestamp - datetime(1970,1,1)).total_seconds()
        now_timestamp_in_iso = datetime.fromtimestamp(int(now_secs_from_epoch)).strftime('%Y-%m-%d_%T')
        return now_timestamp_in_iso

    
    ### log()
    #
    def log(self, target, message):
        message = '['+self.now_ISOish()+'] '+message
        if target is not None:
            target.append(message)
        print(message)
        sys.stdout.flush()

    #END_CLASS_HEADER
    
    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        
        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.ws_url = config['workspace-url']
        self.ws = Workspace(self.ws_url)
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass

    def run_kb_cdm_genome_match(self, ctx, params):
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN run_kb_cdm_genome_match

        # Print statements to stdout/stderr are captured and available as the App log
        logging.info('Starting run_kb_cdm_genome_match function. Params=' + pformat(params))

        genomeset_ref = params['genomeset_ref']
        output_directory = os.path.join(self.shared_folder, "output_cdm_match")
        workspace = params['workspace_name']

        # Setting up GTDB run

        """

        if params['run_gtdb'] == 1:
            gtdb_params = {
                "workspace_id": params['workspace_id'],
                "input_object_ref": genomeset_ref,
                "output_tree_basename": "GTDB_Tree",
                "copy_proximals": "0",
                "save_trees": "0",
                "min_perc_aa": 10,
                "db_ver": "214",
                "keep_intermediates": "0",
                "overwrite_tax": "1",
                "dendrogram_report": "0"
            }
        
            gtdb_util = kb_gtdbtk(self.callback_url)
            gtdb_report = gtdb_util.run_kb_gtdbtk_classify_wf(gtdb_params)

            print ("report follows")
            print (gtdb_report)
        else:
            logging.info('Not running GTDB')


        #genomeset_ref = "75058/2/2"
        #genomeset_ref = params['genomeset_ref']

        logging.info('Finding GTDB Taxonomy informtaion in Genomes')
        
        processor = GenomeSetProcessor(ctx['token'], self.ws_url)
        gtdb_updated_genomeset_ref = processor.get_updated_genomeset_ref(genomeset_ref)
        
        parsed_data = processor.fetch_genomeset_data(gtdb_updated_genomeset_ref)
        json_path = processor.generate_json(parsed_data, output_directory)
        html_path = processor.generate_html(parsed_data, output_directory)
        print(f"JSON file is saved at: {json_path}")
        print(f"Interactive HTML file is saved in: {html_path}")
        """


        # Running fastani

        # Fetch the GenomeSet object
        genomeset_object = self.ws.get_objects2({
            "objects": [{"ref": genomeset_ref}]
        })

        # Extract the genome elements
        genome_refs = list()
        genome_in_set =genomeset_object["data"][0]["data"]["elements"]
        for g in genome_in_set:
            ref = genome_in_set[g]['ref']
            genome_refs.append(ref)
                           


        print (genome_refs)

        genome_refs = ['75058/39/1', '75058/17/2']
        os.makedirs(output_directory, exist_ok=True)
        paths = download_fasta(genome_refs, self.callback_url)
        output_paths = run_fast_ani_pairwise(output_directory, paths)

        print (output_paths)
        result_data = get_result_data(output_paths, debug=False)
        output = create_report(self.callback_url, output_directory, workspace, result_data)
        print (output)





        logging.info('Saving report')

        report_creator = HTMLReportCreator(self.callback_url)
        output = report_creator.create_html_report(output_directory, workspace)

        print (output)

 
 



        #END run_kb_cdm_genome_match
        

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_cdm_genome_match return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
