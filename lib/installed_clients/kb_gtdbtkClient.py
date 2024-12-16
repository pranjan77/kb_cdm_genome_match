# -*- coding: utf-8 -*-
############################################################
#
# Autogenerated by the KBase type compiler -
# any changes made here will be overwritten
#
############################################################

from __future__ import print_function
# the following is a hack to get the baseclient to import whether we're in a
# package or not. This makes pep8 unhappy hence the annotations.
try:
    # baseclient and this client are in a package
    from .baseclient import BaseClient as _BaseClient  # @UnusedImport
except ImportError:
    # no they aren't
    from baseclient import BaseClient as _BaseClient  # @Reimport


class kb_gtdbtk(object):

    def __init__(
            self, url=None, timeout=30 * 60, user_id=None,
            password=None, token=None, ignore_authrc=False,
            trust_all_ssl_certificates=False,
            auth_svc='https://ci.kbase.us/services/auth/api/legacy/KBase/Sessions/Login',
            service_ver='release',
            async_job_check_time_ms=100, async_job_check_time_scale_percent=150, 
            async_job_check_max_time_ms=300000):
        if url is None:
            raise ValueError('A url is required')
        self._service_ver = service_ver
        self._client = _BaseClient(
            url, timeout=timeout, user_id=user_id, password=password,
            token=token, ignore_authrc=ignore_authrc,
            trust_all_ssl_certificates=trust_all_ssl_certificates,
            auth_svc=auth_svc,
            async_job_check_time_ms=async_job_check_time_ms,
            async_job_check_time_scale_percent=async_job_check_time_scale_percent,
            async_job_check_max_time_ms=async_job_check_max_time_ms)

    def run_kb_gtdbtk(self, params, context=None):
        """
        Run GTDB-tk Classify (deprecated method name)
        :param params: instance of type "GTDBtk_Classify_Params" (Parameters
           for the GTDB-tk Classify (classify_wf) run. Required:
           input_object_ref: A reference to the workspace object to process.
           workspace_id: The integer workspace ID where the results will be
           saved. Optional: min_perc_aa: the minimum sequence alignment as a
           percent, default 10.) -> structure: parameter "workspace_id" of
           Long, parameter "input_object_ref" of String, parameter
           "output_tree_basename" of String, parameter "copy_proximals" of
           type "bool", parameter "save_trees" of type "bool", parameter
           "min_perc_aa" of Double, parameter "db_ver" of Long, parameter
           "keep_intermediates" of type "bool", parameter "overwrite_tax" of
           type "bool", parameter "dendrogram_report" of type "bool"
        :returns: instance of type "ReportResults" (The results of the
           GTDB-tk run. report_name: The name of the report object in the
           workspace. report_ref: The UPA of the report object, e.g.
           wsid/objid/ver.) -> structure: parameter "report_name" of String,
           parameter "report_ref" of String
        """
        return self._client.run_job('kb_gtdbtk.run_kb_gtdbtk',
                                    [params], self._service_ver, context)

    def run_kb_gtdbtk_classify_wf(self, params, context=None):
        """
        Run GTDB-tk Classify
        :param params: instance of type "GTDBtk_Classify_Params" (Parameters
           for the GTDB-tk Classify (classify_wf) run. Required:
           input_object_ref: A reference to the workspace object to process.
           workspace_id: The integer workspace ID where the results will be
           saved. Optional: min_perc_aa: the minimum sequence alignment as a
           percent, default 10.) -> structure: parameter "workspace_id" of
           Long, parameter "input_object_ref" of String, parameter
           "output_tree_basename" of String, parameter "copy_proximals" of
           type "bool", parameter "save_trees" of type "bool", parameter
           "min_perc_aa" of Double, parameter "db_ver" of Long, parameter
           "keep_intermediates" of type "bool", parameter "overwrite_tax" of
           type "bool", parameter "dendrogram_report" of type "bool"
        :returns: instance of type "ReportResults" (The results of the
           GTDB-tk run. report_name: The name of the report object in the
           workspace. report_ref: The UPA of the report object, e.g.
           wsid/objid/ver.) -> structure: parameter "report_name" of String,
           parameter "report_ref" of String
        """
        return self._client.run_job('kb_gtdbtk.run_kb_gtdbtk_classify_wf',
                                    [params], self._service_ver, context)

    def status(self, context=None):
        return self._client.run_job('kb_gtdbtk.status',
                                    [], self._service_ver, context)