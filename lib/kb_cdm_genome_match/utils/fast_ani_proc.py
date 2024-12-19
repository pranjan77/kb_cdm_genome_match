# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import multiprocessing

# This module provides a way to run the fastANI binary, pass
# in data, and read the output


def run_fast_ani_pairwise(scratch, paths):
    """
    Given a list of assembly paths, run fastANI on every pair
    Runs in parallel on each cpu
    :param scratch: string path where to put all output
    :param paths: list of paths to each assembly file (fasta format)
    :returns: array of output result paths
    """
    # We have to cap cpus at 2 so we dont overuse our container node's resources
    # If we only have 1 cpu available, it will just run serial but threaded
    pool = multiprocessing.Pool(processes=2)
    jobs = []
    for p1 in paths:
        for p2 in paths:
            if p1 == p2:
                continue
            jobs.append(pool.apply_async(_run_proc, (scratch, p1, p2)))
    out_paths = [j.get() for j in jobs]
    return out_paths


def _run_proc(scratch, path1, path2):
    """
    :param scratch: file path of the scratch directory
    :param path1: path for the query genome file
    :param path2: path for the reference genome file
    :returns: output file path
    """
    out_name = os.path.basename(path1) + '-' + os.path.basename(path2) + '.out'
    out_path = os.path.join(scratch, out_name)
    args = ['fastANI', '-q', path1, '-r', path2, '--visualize', '-o', out_path, '--threads', '2']
    try:
        _run_subprocess(args, 'fastANI')
    except OSError as err:
        print(('Error running fastANI:', str(err), 'with args:', args))
        raise err
    except Exception:
        print(('Unexpected error:', sys.exc_info()[0], 'with args:', args))
    _visualize(path1, path2, out_path)
    return out_path


def _visualize(path1, path2, out_path):
    """
    Given the output path for a fastANI result, build the PDF visualization file using Rscript
    $ Rscript scripts/visualize.R B_quintana.fna B_henselae.fna fastani.out.visual
    """
    r_path = os.path.join(os.path.dirname(__file__), 'scripts', 'visualize.R')
    script_path = os.path.abspath(r_path)
    args = ['Rscript', script_path, path1, path2, out_path + '.visual']

    try:
        _run_subprocess(args, 'Rscript visualization')
    except OSError as err:
        print(('Error running visualizer:', str(err), 'with args:', args))
        raise err
    except Exception:
        print(('Unexpected error:', sys.exc_info()[0], 'with args:', args))


def _run_subprocess(args, proc_name):
    """Run a sub-process, logging stdout/err."""
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    print(('=' * 80))
    # Note that neither fastANI nor Rscript seem to make use of stdout/err properly. fastANI prints
    # all results to stderr
    print(('Results for ' + proc_name))
    print(stdout)
    print(stderr)
    print(('=' * 80))
