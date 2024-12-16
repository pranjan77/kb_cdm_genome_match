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



        genomeset_ref = params['input_object_ref']
        workspace = params['workspace_name']
        processor = GenomeSetProcessor(ctx['token'], self.ws_url)
        output_directory = os.path.join(self.shared_folder, "output")
        parsed_data = processor.fetch_genomeset_data(genomeset_ref)
        json_path = processor.generate_json(parsed_data, output_directory)
        html_path = processor.generate_html(parsed_data, output_directory)
        print(f"JSON file is saved at: {json_path}")
        print(f"Interactive HTML file is saved in: {html_path}")

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
