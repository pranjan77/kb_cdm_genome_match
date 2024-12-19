# -*- coding: utf-8 -*-
import os
from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader('kb_cdm_genome_match', 'utils/templates'),
    autoescape=select_autoescape(['html'])
)

# Construct some pretty-ish output for FastANI


def get_result_data(output_paths, debug=False):
    """
    Create a list of objects of all the result data from running fastani
    """
    result_data = []
    for path in output_paths:
        with open(path) as file:
            contents = file.read()
            parts = contents[:-1].split("\t")
            if len(parts) >= 5:
                result_data.append({
                    'query_path': __filename(parts[0]),
                    'reference_path': __filename(parts[1]),
                    'percentage_match': parts[2],
                    'orthologous_matches': parts[3],
                    'total_fragments': parts[4],
                    'viz_path': path + '.visual.pdf',
                    'viz_filename': os.path.basename(path) + '.visual.pdf'
                })
                if debug:
                    print("=" * 8  + " " + path + " " + "=" * 8)
                    print(result_data[-1])
            else:
                print(('Invalid results from fastANI: ' + contents))
    result_data = sorted(result_data, key=lambda r: float(r['percentage_match']))
    return result_data


def create_html_tables(result_data):
    """
    For each result, create an html table for it
    """
    headers = ['Query', 'Reference', 'ANI Estimate', 'Matches',
               'Total', 'Visualization']
    template = env.get_template('result_tables.html')
    return template.render(headers=headers, results=result_data)


def __filename(path):
    "Return the filename, without extension, of a full path"
    return os.path.splitext(os.path.basename(path))[0]
