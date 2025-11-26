#!/usr/bin/env python3
"""
Example script for submitting multi-bunch instability scans using jobsmith.

This script demonstrates how to use the jobsmith module to submit parameter
scans for coupled-bunch instability simulations (TCBI).

Usage:
    python example_tcbi_scan.py --dry-run  # Preview jobs without submitting
    python example_tcbi_scan.py            # Submit jobs to CCRT
    python example_tcbi_scan.py --mode slurm  # Submit to SLURM instead
"""

import argparse
import numpy as np
import sys
import os

# Add src directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobsmith import Job, submit_scan, ParameterGrid


# Default paths for CCRT
SRC_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/"
DATA_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/"
MACHINE_DATA_FOLDER = "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/"
SCRIPT_PATH = "/home/dockeruser/transverse_instabilities/src/simulation/track_mb.py"
PYTHON_PATH = "/home/dockeruser/venv/bin/python3"
IMAGE_NAME = "soleil-pa:mbtrack2"


def make_multibunch_job(params):
    """
    Create a Job for multi-bunch tracking from scan parameters.
    
    Args:
        params: Dictionary containing simulation parameters
        
    Returns:
        Job instance configured for multi-bunch tracking
    """
    # Build command string with -u for unbuffered output
    command_parts = [
        PYTHON_PATH,
        "-u",  # Unbuffered output for MPI
        SCRIPT_PATH,
        f"--n_macroparticles {params.get('n_macroparticles', 100000)}",
        f"--n_turns {params.get('n_turns', 100000)}",
        f"--n_bin {params.get('n_bin', 100)}",
        f"--bunch_current {params['bunch_current']}",
        f"--Qp_x {params.get('Qp_x', params.get('chromaticity', 1.6))}",
        f"--Qp_y {params.get('Qp_y', params.get('chromaticity', 1.6))}",
        f"--id_state {params.get('id_state', 'close')}",
        f"--include_Zlong {params.get('include_Zlong', 'True')}",
        f"--harmonic_cavity {params.get('harmonic_cavity', 'False')}",
        f"--n_turns_wake {params.get('n_turns_wake', 50)}",
        f"--max_kick {params.get('max_kick', 0)}",
        f"--sc {params.get('sc', 'False')}",
        f"--ibs {params.get('ibs', 'True')}",
        f"--quad {params.get('quad', 'False')}",
    ]
    command = " ".join(command_parts)
    
    # Generate descriptive job name
    chromaticity = params.get('Qp_y', params.get('chromaticity', 1.6))
    job_name = (
        f"tcbi_Qp={chromaticity:.1f}"
        f"_{params['bunch_current']:.1e}"
        f"_sc={params.get('sc', 'False')}"
    )
    
    return Job(
        name=job_name,
        command=command,
        time_limit=params.get('job_time', 86000),
        n_tasks=params.get('n_tasks', 416),
        n_cpus_per_task=1,
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
        description="Submit multi-bunch instability parameter scan"
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
    # This example scans chromaticity at fixed current
    param_grid = ParameterGrid({
        'chromaticity': np.linspace(0.2, 3.0, 15),
        'bunch_current': [1.2e-3],
        'include_Zlong': ['True'],
        'harmonic_cavity': ['False', 'True'],
        'sc': ['True', 'False'],
        'ibs': ['True'],
        'n_turns_wake': [50],
        'id_state': ['close'],
    })
    
    print(f"Submitting {len(param_grid)} jobs to {args.mode.upper()}...")
    if args.dry_run:
        print("(DRY RUN - no jobs will be submitted)")
    
    # Submit the scan
    job_ids = submit_scan(
        args.mode,
        param_grid,
        make_multibunch_job,
        dry_run=args.dry_run,
    )
    
    # Report results
    successful = sum(1 for jid in job_ids if jid is not None)
    print(f"\nSubmitted {successful}/{len(job_ids)} jobs successfully")


if __name__ == "__main__":
    main()
