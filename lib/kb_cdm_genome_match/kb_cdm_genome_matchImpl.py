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


from installed_clients.AssemblyUtilClient import AssemblyUtil

from kb_cdm_genome_match.core.api_translation import get_cdm_genome_match_params
from kb_cdm_genome_match.core.html_report_creator import HTMLReportCreator
from kb_cdm_genome_match.core.genomeset_processor import GenomeSetProcessor
from kb_cdm_genome_match.core.kb_client_set import KBClients
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.kb_gtdbtkClient import kb_gtdbtk

from .utils2.mash_skani_multiple import mash_skani_pipeline
from .utils2.append_sample_information import merge_mash_skani_with_sample
from .utils2.create_html import create_datatable_html

from .utils.fast_ani_processor import process_genomes
from .utils.fast_ani_processor import parse_and_write_fastani_output
from .utils.fast_ani_processor import prepare_html
from .utils.fast_ani_processor import get_taxonomy_all_refs 


from .utils.fast_ani_proc import run_fast_ani_pairwise
from .utils.fast_ani_output import get_result_data
from .utils.downloader import download_fasta
from .utils.fast_ani_report import create_report

from .utils.taxonomy_matcher import find_related_genomes_multiple

from .utils.assembly_saver import KBaseAssemblyManager


from .utils2.KBaseObjectUtils import download_fasta_files
from .utils2.mash_skani_multiple import mash_skani_pipeline



from installed_clients.WorkspaceClient import Workspace


#END_HEADER


class kb_cdm_genome_match:
    '''
    Module Name:
    kb_cdm_genome_match

    Module Description:
    A KBase module: kb_cdm_genome_match
This sample module contains one small method that filters contigs.
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "git@github.com:pranjan77/kb_cdm_genome_match.git"
    GIT_COMMIT_HASH = "c1e154f8441731d832ebae3339861c9d6586a7fb"

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
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_cdm_genome_match

        # Print statements to stdout/stderr are captured and available as the App log
        logging.info('Starting run_kb_cdm_genome_match function. Params=' + pformat(params))

        genomeset_ref = params['genomeset_ref']
        max_count = params['max_count']
        max_level = params['max_level']

        output_directory = os.path.join(self.shared_folder, "output_cdm_match")
        os.makedirs(output_directory, exist_ok=True)
        workspace = params['workspace_name']

        # Setting up GTDB run if all genomes in genomeset has not been updated with GTDB taxonomy
        #TODO: Manually taking input right now but should handle it automatically
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

        logging.info('Finding GTDB Taxonomy informtaion in Genomes')


        
        processor = GenomeSetProcessor(ctx['token'], self.ws_url)
        # Only relevant when input genomeset_ref when run through gtdb workflow
        # is saved as genomeset with same name but a new ref.
        gtdb_updated_genomeset_ref = processor.get_updated_genomeset_ref(genomeset_ref)
        
         
        genomeset_taxonomy_data = processor.fetch_genomeset_data(gtdb_updated_genomeset_ref)
        taxon_assignments = [genome['gtdb_lineage'] for genome in genomeset_taxonomy_data]



        logging.info (taxon_assignments)
        outx, related_genomes_only_dict = find_related_genomes_multiple(taxon_assignments, max_count, max_level)
        logging.info (outx)
        logging.info (genomeset_taxonomy_data)
        logging.info (related_genomes_only_dict)
        output = dict()
        allpaths, related_path_dict = process_genomes(genomeset_taxonomy_data, related_genomes_only_dict, output_directory, self.callback_url)
        taxonomy_dict = get_taxonomy_all_refs (genomeset_taxonomy_data, related_genomes_only_dict)
        output_csv_path = os.path.join(output_directory, "output.csv")
        output_html = os.path.join(output_directory, "index.html")
        parse_and_write_fastani_output(allpaths, related_path_dict, taxonomy_dict, output_csv_path)
        prepare_html(output_csv_path, output_html)
        logging.info (output_html)
        logging.info (output_csv_path)
        logging.info ("allpaths" + pformat(allpaths))

        scratch_dir = os.path.join(self.shared_folder, "assemblies") 
        manager = KBaseAssemblyManager(workspace, self.callback_url, ctx['token'], scratch_dir)
        manager.save_assemblies_from_csv(output_csv_path)
        objects_created = manager.print_assembly_mapping()


        report_creator = HTMLReportCreator(self.callback_url)
        output = report_creator.create_html_report(output_directory, workspace, objects_created, output_csv_path)
        logging.info (output)



        #END run_kb_cdm_genome_match

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_cdm_genome_match return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_mash_skani(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """


        # ctx is the context object
        # return variables are: output
        #BEGIN run_mash_skani
        #query_fasta = "/data/GTDB_v214/GCA/018/630/425/GCA_018630425.1_ASM1863042v1/GCA_018630425.1_ASM1863042v1_genomic.fna.gz "
        #mash_sketch_db = "/sketches/sketch_output/temp_sketches/combined_gtdb_sketch_410303_genome.msh"
        #query_genome1 = "/data/GTDB_v214/GCA/018/630/425/GCA_018630425.1_ASM1863042v1/GCA_018630425.1_ASM1863042v1_genomic.fna.gz"
        #query_genome2 = "/data/GTDB_v214/GCA/018/263/505/GCA_018263505.1_ASM1826350v1/GCA_018263505.1_ASM1826350v1_genomic.fna.gz"
        #mash_database = "/sketches/sketch_output/temp_sketches/combined_gtdb_sketch_410303_genome.msh"

        logging.info('Starting run_kb_cdm_genome_match function. Params=' + pformat(params))
        provenance = ctx['provenance']


        ref_list = params['ref_list']
        max_count = params['max_count']
        max_mash_dist = params['max_mash_dist']
        min_ani = params['min_ani']
        workspace_name = params['workspace_name']



        logging.info ("=======Downloading fasta files============")
        ref_fasta_path_dict = download_fasta_files(self.callback_url, ref_list)
        logging.info (ref_fasta_path_dict)


        mash_db = "/data/datafiles/datafiles/sketches/combined_gtdb_sketch_410303_genome.msh"
        taxonomy_file = "/data/datafiles/datafiles/genome_taxonomy_data/cdm_genomes_paths_taxonomy.tsv"
        genome_sample_file = "/data/datafiles/datafiles/sample_info/genome_sample.csv"


        output_directory = os.path.join(self.shared_folder, "skani_mash_sample")
        os.makedirs(output_directory, exist_ok=True)

        skani_mash_csv = os.path.join(output_directory, "skani_mash.csv")
        skani_mash_sample_csv = os.path.join(output_directory, "skani_mash_sample.csv")
        output_html = os.path.join(output_directory, "index.html")



        logging.info ("=======Running mash and skani pipeline============")
        mash_skani_pipeline(ref_fasta_path_dict, mash_db, taxonomy_file, self.ws_url, 
                             workspace_name, provenance, max_count, max_mash_dist, min_ani,skani_mash_csv)


        logging.info ("=======Getting sample information============")

        merge_mash_skani_with_sample(skani_mash_csv, genome_sample_file, skani_mash_sample_csv)

        logging.info ("Generating HTML")
        create_datatable_html(skani_mash_sample_csv, output_html, rows_per_page=10)

        logging.info ("=======Creating report============")

        report_creator = HTMLReportCreator(self.callback_url)
        objects_created = []
        output = report_creator.create_html_report(output_directory, workspace_name, objects_created, skani_mash_sample_csv)
        logging.info (output)
        #END run_mash_skani

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_mash_skani return value ' +
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
