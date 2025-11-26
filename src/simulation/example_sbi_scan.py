#!/usr/bin/env python3
"""
Example script for submitting single-bunch instability scans using jobsmith.

This script demonstrates how to use the jobsmith module to submit parameter
scans for single-bunch transverse instability simulations.

Usage:
    python example_sbi_scan.py --dry-run  # Preview jobs without submitting
    python example_sbi_scan.py            # Submit jobs to CCRT
    python example_sbi_scan.py --mode slurm  # Submit to SLURM instead
"""

import argparse
import numpy as np
import sys
import os

# Add src directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobsmith import Job, submit_scan, ParameterGrid, get_submitter


# Default paths for CCRT
SRC_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/"
DATA_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/"
MACHINE_DATA_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/"
SCRIPT_PATH = "/home/dockeruser/transverse_instabilities/src/simulation/track_TI.py"
PYTHON_PATH = "/home/dockeruser/venv/bin/python3"
IMAGE_NAME = "soleil-pa:mbtrack2"


def make_single_bunch_job(params):
    """
    Create a Job for single-bunch tracking from scan parameters.
    
    Args:
        params: Dictionary containing simulation parameters
        
    Returns:
        Job instance configured for single-bunch tracking
    """
    # Build command string
    command_parts = [
        PYTHON_PATH,
        SCRIPT_PATH,
        f"--n_macroparticles {params.get('n_macroparticles', 500000)}",
        f"--n_turns {params.get('n_turns', 50000)}",
        f"--n_bin {params.get('n_bin', 100)}",
        f"--bunch_current {params['bunch_current']}",
        f"--Qp_x {params.get('Qp_x', params.get('chromaticity', 0.0))}",
        f"--Qp_y {params.get('Qp_y', params.get('chromaticity', 0.0))}",
        f"--id_state {params.get('id_state', 'close')}",
        f"--include_Zlong {params.get('include_Zlong', 'True')}",
        f"--harmonic_cavity {params.get('harmonic_cavity', 'False')}",
        f"--max_kick {params.get('max_kick', 0)}",
        f"--sc {params.get('sc', 'False')}",
        f"--ibs {params.get('ibs', 'False')}",
        f"--quad {params.get('quad', 'False')}",
        f"--wake_y {params.get('wake_y', 'True')}",
    ]
    command = " ".join(command_parts)
    
    # Generate descriptive job name
    job_name = (
        f"sbi_{params['bunch_current']:.1e}"
        f"_sc={params.get('sc', 'False')}"
        f"_hc={params.get('harmonic_cavity', 'False')}"
        f"_Z={params.get('include_Zlong', 'True')}"
    )
    
    return Job(
        name=job_name,
        command=command,
        time_limit=params.get('job_time', 85000),
        n_tasks=1,
        n_cpus_per_task=8,
        image=IMAGE_NAME,
        modules=["mpi/openmpi/4.1.4"],
        mounts={
            SRC_FOLDER: "/home/dockeruser/transverse_instabilities/src/",
            MACHINE_DATA_FOLDER: "/home/dockeruser/facilities_mbtrack2/",
            DATA_FOLDER: "/home/dockeruser/transverse_instabilities/data/",
        },
    )


def main():
    parser = argparse.ArgumentParser(
        description="Submit single-bunch instability parameter scan"
    )
    parser.add_argument(
        "--mode",
        choices=["ccrt", "slurm"],
        default="ccrt",
        help="Submission mode (default: ccrt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview jobs without submitting",
    )
    args = parser.parse_args()
    
    # Define parameter grid for the scan
    # This example scans over bunch current with various physics options
    param_grid = ParameterGrid({
        'bunch_current': 1e-3 * np.linspace(0.2, 6, 30),
        'include_Zlong': ['True'],
        'harmonic_cavity': ['False', 'True'],
        'sc': ['True'],
        'ibs': ['True'],
        'chromaticity': [0.0],
        'quad': ['False', 'True'],
        'wake_y': ['True'],
        'id_state': ['close'],
    })
    
    print(f"Submitting {len(param_grid)} jobs to {args.mode.upper()}...")
    if args.dry_run:
        print("(DRY RUN - no jobs will be submitted)")
    
    # Submit the scan
    job_ids = submit_scan(
        args.mode,
        param_grid,
        make_single_bunch_job,
        dry_run=args.dry_run,
    )
    
    # Report results
    successful = sum(1 for jid in job_ids if jid is not None)
    print(f"\nSubmitted {successful}/{len(job_ids)} jobs successfully")


if __name__ == "__main__":
    main()
