"""
Deprecated submission module - use jobsmith instead.

This module is deprecated and will be removed in a future release.
Please migrate to the jobsmith package for job submission functionality.

Example migration:
    # Old way (deprecated):
    from submission.submission import write_submission_script
    
    # New way:
    from jobsmith import Job, CCRTSubmitter
    job = Job(name="my_job", command="python script.py", time_limit=86000)
    submitter = CCRTSubmitter()
    submitter.submit(job)
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "The 'submission' module is deprecated and will be removed in a future release. "
    "Please use 'jobsmith' instead. See README.md for migration instructions.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export jobsmith components for backwards compatibility
try:
    from jobsmith import Job, Submitter, CCRTSubmitter, SLURMSubmitter, submit_scan, ParameterGrid
except ImportError:
    # Fall back to local jobsmith if not installed
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from jobsmith import Job, Submitter, CCRTSubmitter, SLURMSubmitter, submit_scan, ParameterGrid

__all__ = ['Job', 'Submitter', 'CCRTSubmitter', 'SLURMSubmitter', 'submit_scan', 'ParameterGrid']
