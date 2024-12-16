/*
A KBase module: kb_cdm_genome_match
This sample module contains one small method that filters contigs.
*/

module kb_cdm_genome_match {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kb_cdm_genome_match(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
