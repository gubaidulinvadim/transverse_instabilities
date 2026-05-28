"""jobsmith - Unified job submission interface.

This module provides a unified API for submitting jobs to HPC clusters
(CCRT, SLURM) or running locally.

Main API:
    - Job: Configuration object for a single job
    - Submitter: Handles job submission to different backends
    - submit: Convenience function to submit a single job
    - submit_scan: Submit parameter scan (multiple jobs)

CLI:
    jobsmith submit --config_file config.toml
    jobsmith submit-scan --config_file scan_config.toml [--dry-run]

Example:
    from jobsmith import Job, Submitter, submit, submit_scan

    # Using Job and Submitter classes
    job = Job.from_toml("config.toml")
    submitter = Submitter(server="ccrt")
    submitter.submit(job)

    # Using convenience function
    submit("config.toml")

    # Submit parameter scan
    submit_scan("scan_config.toml", dry_run=False)
"""

from jobsmith.core import Job, Submitter, submit
from jobsmith.scan import submit_scan, expand_scan_values, generate_scan_configs

__all__ = [
    "Job",
    "Submitter",
    "submit",
    "submit_scan",
    "expand_scan_values",
    "generate_scan_configs",
]

__version__ = "1.0.0"
