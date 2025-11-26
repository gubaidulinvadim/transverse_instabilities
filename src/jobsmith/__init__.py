"""
jobsmith - Unified job submission interface for HPC clusters.

This module provides a unified interface for submitting jobs to various
HPC systems (CCRT, SLURM, etc.) and running parameter scans.

Note: This is a local implementation. Once the standalone jobsmith package
is available on PyPI, install it with `pip install jobsmith` and remove
this local module.
"""

from .job import Job
from .submitter import Submitter, CCRTSubmitter, SLURMSubmitter, get_submitter
from .scan import submit_scan, ParameterGrid

__all__ = [
    'Job',
    'Submitter',
    'CCRTSubmitter',
    'SLURMSubmitter',
    'get_submitter',
    'submit_scan',
    'ParameterGrid',
]

__version__ = '0.1.0'
