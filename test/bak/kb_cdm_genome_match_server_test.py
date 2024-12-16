# -*- coding: utf-8 -*-
import hashlib
import os
import requests
import time
import unittest
import uuid
import json
from pathlib import Path
from configparser import ConfigParser
from shutil import copyfile
from shutil import rmtree



from kb_cdm_genome_match.kb_cdm_genome_matchImpl import kb_cdm_genome_match
from kb_cdm_genome_match.kb_cdm_genome_matchServer import MethodContext
from kb_cdm_genome_match.authclient import KBaseAuth as _KBaseAuth

from installed_clients.SetAPIServiceClient import SetAPI
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.WorkspaceClient import Workspace
from installed_clients.AbstractHandleClient import AbstractHandle



WORKDIR = '/kb/module/work/tmp/'


class kb_cdm_genome_matchTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_cdm_genome_match'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(cls.token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': cls.token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_cdm_genome_match',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        
        cls.ws_url = cls.cfg['workspace-url']
        cls.shock_url = cls.cfg['shock-url']
        cls.ws = Workspace(cls.ws_url, token=cls.token)
        cls.serviceImpl = kb_cdm_genome_match(cls.cfg)
        cls.scratch = Path(cls.cfg['scratch']).absolute()
        cls.service_wiz_url = cls.cfg['srv-wiz-url']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        #suffix = int(time.time() * 1000)
        #cls.wsName = "test_gktb_tk_" + str(suffix)
        #ret = cls.ws.create_workspace({'workspace': cls.wsName})
        #cls.wsid = ret[0]
        #print (cls.wsid)

        cls.wsName = "pranjan77:narrative_1734299479897"
        cls.wsid = 75051
        
        cls.hs = AbstractHandle(cls.cfg['handle-service-url'], token=cls.token)
        cls.au = AssemblyUtil(cls.callback_url, token=cls.token)
        cls.dfu = DataFileUtil(cls.callback_url, token=cls.token)
        cls.gfu = GenomeFileUtil(cls.callback_url, token=cls.token)
        cls.setAPI = SetAPI(cls.service_wiz_url, token=cls.token)
        cls.handles_to_delete = []
        cls.nodes_to_delete = []
        #cls.prepare_data()
        

    @classmethod
    def tearDownClass(cls):
        #if hasattr(cls, 'wsName'):
        #    cls.ws.delete_workspace({'workspace': cls.wsName})
        #    print('Test workspace was deleted')
        #if hasattr(cls, 'nodes_to_delete'):
        #    for node in cls.nodes_to_delete:
        #        cls.delete_shock_node(node)
        #if hasattr(cls, 'handles_to_delete'):
        #    if cls.handles_to_delete:
        #        cls.hs.delete_handles(cls.hs.hids_to_handles(cls.handles_to_delete))
        #        print('Deleted handles ' + str(cls.handles_to_delete))
        pass

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shock_url + '/node/' + node_id, headers=header, allow_redirects=True)
        print('Deleted shock node ' + node_id)

    @classmethod
    def ref_from_info(cls, obj_info):
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
        return "/".join([str(obj_info[WSID_I]), str(obj_info[OBJID_I]), str(obj_info[VERSION_I])])

    def isUpa (self, candidate_upa):
        legit_upa = True
        for upa_element in candidate_upa.split('/'):
            if not upa_element.isdigit():
                print ("Error: not UPA element: "+upa_element)
                legit_upa = False
        return legit_upa
        
    @classmethod
    def prepare_data(cls):
        tempdir = cls.scratch / 'tempstuff'
        tempdir.mkdir(parents=True, exist_ok=True)

        # bacterial assemblies
        cls.bac_assy = []
        for this_filename in [ 'Rhodo_contigs.fa.gz',
                               'Bin.001.fa.gz', 
                               'Bin.046.fa.gz', 
                               'Bin.047.fa.gz', 
                               'Bin.049.fa.gz'
                              ]:  
            bac_assyfile = tempdir / this_filename
            copyfile(Path(__file__).parent / 'data' / this_filename, bac_assyfile)
            bac_assy_ref = cls.au.save_assembly_from_fasta(
                {'file': {'path': str(bac_assyfile)},
                 'workspace_name': cls.wsName,  # TODO AU should take an ID
                 'assembly_name': this_filename
                 })
            cls.bac_assy.append(bac_assy_ref)

        # MG assembly
        this_filename = '37AB_metaSPAdes_binnedcontigs.contigs.gz'
        mg_assyfile = tempdir / this_filename
        copyfile(Path(__file__).parent / 'data' / this_filename, mg_assyfile)
        mg_assy = cls.au.save_assembly_from_fasta(
            {'file': {'path': str(mg_assyfile)},
             'workspace_name': cls.wsName,
             'assembly_name': this_filename
             })

        # binned contigs
        this_filename = '37AB_metaSPAdes.binnedcontigs'
        mg_binfile = tempdir / this_filename
        copyfile(Path(__file__).parent / 'data' / this_filename, mg_binfile)
        with open (mg_binfile, 'r') as bin_fh:
            bin_obj = json.load(bin_fh)
        bin_obj['assembly_ref'] = mg_assy
        bin_obj_info = cls.ws.save_objects({
            'workspace': cls.wsName,
            'objects': [
                {
                    'type': 'KBaseMetagenomes.BinnedContigs',
                    'data': bin_obj,
                    'name': this_filename
                }
            ]})[0]
        cls.binned_contigs = cls.ref_from_info(bin_obj_info)

        # 3 archaeal assemblies and genomes, assembly set and genome set
        cls.arch_genomes = []
        cls.arch_assemblies = []
        assembly_items = []
        genome_elements = {}
        for this_genome_id in ['GCF_000007345.1', 'GCF_000008665.1', 'GCF_009428885.1']:
            # DEBUG
            #if this_genome_id == 'GCF_000008665.1':
            #    break
            
            this_gff_filename = this_genome_id + '_genes.gff'
            this_assy_filename = this_genome_id + '_assembly.fa.gz'

            # assembly
            assyfile = tempdir / this_assy_filename
            copyfile(Path(__file__).parent / 'data' / this_assy_filename, assyfile)
            assembly_ref = cls.au.save_assembly_from_fasta(
                {'file': {'path': str(assyfile)},
                 'workspace_name': cls.wsName,
                 'assembly_name': this_assy_filename
                })
            cls.arch_assemblies.append(assembly_ref)
            assembly_items.append({'ref': assembly_ref, 'label': this_genome_id})

            # genome
            gfffile = tempdir / this_gff_filename
            copyfile(Path(__file__).parent / 'data' / this_gff_filename, gfffile)
            genome_ref = cls.gfu.fasta_gff_to_genome (
                { "workspace_name": cls.wsName,
                  "genome_name": this_genome_id,
                  "fasta_file": {"path": str(assyfile)},
                  "gff_file": {"path": str(gfffile)},
                  "source": "GFF",
                  "scientific_name": "Genus_foo species_bar",
                  "generate_missing_genes": "True"                
                })['genome_ref']
            cls.arch_genomes.append(genome_ref)
            genome_elements[this_genome_id] = { 'ref': genome_ref }
            
        # archaeal assemblySet
        assemblySet_name = 'Archaea_3.AssemblySet'
        assemblySet_obj = { 'description': 'AssemblySet for archaeal genomes',
                            'items': assembly_items
        }
        try:
            cls.arch_assemblySet = cls.setAPI.save_assembly_set_v1 (
                {'workspace_name': cls.wsName,
                 'output_object_name': assemblySet_name,
                 'data': assemblySet_obj,
                })['set_ref']
        except Exception as e:
            raise ValueError ("ABORT: unable to save Arc AssemblySet object.\n"+str(e))

        # archaeal genomeSet
        genomeSet_name = 'Archaea_3.GenomeSet'
        genomeSet_obj = {'description': 'Test GS', 'elements': genome_elements }
        try:
            genomeSet_info = cls.ws.save_objects(
                {'workspace': cls.wsName,
                 'objects': [{
                     'type': 'KBaseSearch.GenomeSet',
                     'data': genomeSet_obj,
                     'name': genomeSet_name
                     }]})[0]
        except Exception as e:
            raise ValueError ("ABORT: unable to save Arc GenomeSet object.\n"+str(e))
        cls.arch_genomeSet = cls.ref_from_info(genomeSet_info)

        # challenging bac assemblySet
        assembly_items = []
        for assembly_ref in cls.bac_assy:
            assembly_items.append({'ref': assembly_ref, 'label': assembly_ref})
        assemblySet_name = 'Challenging_Bacs.AssemblySet'
        assemblySet_obj = { 'description': 'AssemblySet for Challenging Bac assemblies',
                            'items': assembly_items
                           }
        try:
            cls.bac_assemblySet = cls.setAPI.save_assembly_set_v1 (
                {'workspace_name': cls.wsName,
                 'output_object_name': assemblySet_name,
                 'data': assemblySet_obj,
                 })['set_ref']
        except Exception as e:
            raise ValueError ("ABORT: unable to save Bac AssemblySet object.\n"+str(e))

        # mixed bac and arc assemblySet
        assembly_items = []
        for assembly_ref in cls.bac_assy:
            assembly_items.append({'ref': assembly_ref, 'label': assembly_ref})
        for assembly_ref in cls.arch_assemblies:
            assembly_items.append({'ref': assembly_ref, 'label': assembly_ref})
        assemblySet_name = 'Mixed_Bac_and_Arc.AssemblySet'
        assemblySet_obj = { 'description': 'AssemblySet for Mixed Bac and Arc assemblies',
                            'items': assembly_items
                           }
        try:
            cls.mixed_assemblySet = cls.setAPI.save_assembly_set_v1 (
                {'workspace_name': cls.wsName,
                 'output_object_name': assemblySet_name,
                 'data': assemblySet_obj,
                 })['set_ref']
        except Exception as e:
            raise ValueError ("ABORT: unable to save Bac AssemblySet object.\n"+str(e))


    @classmethod
    def clean_scratch_dir(cls):
        for inode in os.listdir(cls.scratch):
            path = os.path.join (cls.scratch, inode)
            if os.path.isdir(path):
                rmtree (path)
            else:
                os.remove (path)


    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_run_kb_cdm_genome_match_ok(self):
        # call your implementation
        
        self.clean_scratch_dir()
        report = self.serviceImpl.run_kb_cdm_genome_match(self.ctx, { \
                                                                'workspace_name': self.wsName,
                                                                'genomeset_ref': "75051/19/2",
                                                                'output_tree_basename': 'CDM_Match_Tree',
                                                                'copy_proximals': 0,
                                                                'save_trees': 0,
                                                                'db_ver': 214,
                                                                'keep_intermediates': 0,
                                                                'dendrogram_report': 0         
                                                            })[0]
        #assert self.isUpa (report['report_ref'])

 
 