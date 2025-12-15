"""Core job submission classes and functions.

This module provides the main Job and Submitter classes for the jobsmith
submission system.
"""

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

from jobsmith.utils import load_config, validate_config


@dataclass
class Job:
    """Configuration object for a single job.

    Attributes:
        name: Job name (used for output/error file names).
        time: Maximum job time in seconds.
        n_cpu: Number of CPUs to allocate.
        partition: HPC partition to use.
        err_folder: Folder for error logs.
        out_folder: Folder for output logs.
        is_gpu: Whether GPU resources are needed.
        container: Container image name.
        mount_source: List of source paths for container mounts.
        mount_destination: List of destination paths for container mounts.
        server: Server type ('ccrt', 'slurm', or 'local').
        script_name: Path to the simulation script.
        script_params: Dictionary of script parameters.
    """
    name: str = "job"
    time: int = 86000
    n_cpu: int = 24
    partition: str = "milan"
    err_folder: str = "/ccc/work/cont003/soleil/gubaiduv/err/"
    out_folder: str = "/ccc/work/cont003/soleil/gubaiduv/out/"
    is_gpu: bool = False
    container: str = ""
    mount_source: list = field(default_factory=lambda: ["/ccc/work/cont003/soleil/gubaiduv/bii_tracking/"])
    mount_destination: list = field(default_factory=lambda: ["/home/dockeruser/bii_tracking"])
    server: str = "ccrt"
    script_name: str = "/home/dockeruser/bii_tracking/src/simulation/track_bii.py"
    script_params: dict = field(default_factory=dict)
    config_file: Optional[str] = None

    @classmethod
    def from_toml(cls, config_file: str) -> "Job":
        """Create a Job from a TOML configuration file.

        Args:
            config_file: Path to the .toml configuration file.

        Returns:
            Job instance with configuration from the file.
        """
        config = load_config(config_file)
        validate_config(config, config_file)

        env = config.get('environment', {})
        job_config = config.get('job', {})
        script = config.get('script', {})

        return cls(
            name=job_config.get('name', 'job'),
            time=job_config.get('time', 86000),
            n_cpu=job_config.get('n_cpu', 24),
            partition=job_config.get('partition', 'milan'),
            err_folder=job_config.get('err_folder', '/ccc/work/cont003/soleil/gubaiduv/err/'),
            out_folder=job_config.get('out_folder', '/ccc/work/cont003/soleil/gubaiduv/out/'),
            is_gpu=job_config.get('is_gpu', False),
            container=env.get('container', ''),
            mount_source=env.get('mount_source', ['/ccc/work/cont003/soleil/gubaiduv/bii_tracking/']),
            mount_destination=env.get('mount_destination', ['/home/dockeruser/bii_tracking']),
            server=env.get('server', 'ccrt'),
            script_name=script.get('name', '/home/dockeruser/bii_tracking/src/simulation/track_bii.py'),
            script_params=script,
            config_file=config_file,
        )

    @classmethod
    def from_dict(cls, config: dict) -> "Job":
        """Create a Job from a configuration dictionary.

        Args:
            config: Configuration dictionary with environment, job, and script sections.

        Returns:
            Job instance with configuration from the dictionary.
        """
        env = config.get('environment', {})
        job_config = config.get('job', {})
        script = config.get('script', {})

        return cls(
            name=job_config.get('name', 'job'),
            time=job_config.get('time', 86000),
            n_cpu=job_config.get('n_cpu', 24),
            partition=job_config.get('partition', 'milan'),
            err_folder=job_config.get('err_folder', '/ccc/work/cont003/soleil/gubaiduv/err/'),
            out_folder=job_config.get('out_folder', '/ccc/work/cont003/soleil/gubaiduv/out/'),
            is_gpu=job_config.get('is_gpu', False),
            container=env.get('container', ''),
            mount_source=env.get('mount_source', ['/ccc/work/cont003/soleil/gubaiduv/bii_tracking/']),
            mount_destination=env.get('mount_destination', ['/home/dockeruser/bii_tracking']),
            server=env.get('server', 'ccrt'),
            script_name=script.get('name', '/home/dockeruser/bii_tracking/src/simulation/track_bii.py'),
            script_params=script,
        )


class Submitter:
    """Handles job submission to different backends (CCRT, SLURM, local).

    Attributes:
        server: Server type ('ccrt', 'slurm', or 'local').
    """

    def __init__(self, server: str = "ccrt"):
        """Initialize the submitter.

        Args:
            server: Server type ('ccrt', 'slurm', or 'local').
        """
        self.server = server

    def _get_command_string(self, config_file: str, script_name: str) -> str:
        """Generate the command string for running the simulation script.

        Args:
            config_file: Path to the .toml configuration file.
            script_name: Path to the simulation script.

        Returns:
            Command string to execute the simulation.
        """
        return f'/home/dockeruser/venv/bin/python3 {script_name} --config_file {config_file}\n'

    def _write_submission_script(self, job: Job, config_file: str) -> str:
        """Write a temporary submission script based on the job configuration.

        Args:
            job: Job configuration object.
            config_file: Path to the .toml configuration file.

        Returns:
            Path to the generated job script.
        """
        command_string = self._get_command_string(config_file, job.script_name)

        with open(job.name, "w") as f:
            f.write("#!/bin/bash\n")
            if self.server == 'ccrt':
                # Safely access mount paths with defaults
                src_folder = job.mount_source[0] if job.mount_source else ""
                src_dest = job.mount_destination[0] if job.mount_destination else ""
                data_folder = job.mount_source[1] if len(job.mount_source) > 1 else src_folder
                data_dest = job.mount_destination[1] if len(job.mount_destination) > 1 else src_dest
                f.write("#MSUB -m work,scratch\n")
                if job.is_gpu:
                    f.write("#MSUB -q a100\n")
                else:
                    f.write(f"#MSUB -q {job.partition}\n")
                f.write("#MSUB -Q long\n")
                f.write("#MSUB -n 1\n")
                f.write(f"#MSUB -c {job.n_cpu}\n")
                f.write(f"#MSUB -T {job.time}\n")
                f.write("#MSUB -A soldai\n")
                f.write("#MSUB -@ vadim.gubaidulin@synchrotron-soleil.fr:begin,end,requeue\n")
                # Note: -o and -e appear swapped but this matches original behavior
                f.write(f"#MSUB -o {job.err_folder}{job.name}.err\n")
                f.write(f"#MSUB -e {job.out_folder}{job.name}.out\n")
                f.write('module purge\n')
                if job.is_gpu:
                    f.write(
                        f"ccc_mprun -C {job.container} -E'--ctr-mount src={src_folder},dst={src_dest}:src={data_folder},dst={data_dest}' -E'--ctr-module nvidia' -- "
                        + command_string)
                else:
                    f.write(
                        f"ccc_mprun -C {job.container} -E'--ctr-mount src={src_folder},dst={src_dest}:src={data_folder},dst={data_dest}' -- "
                        + command_string)
            elif self.server == 'slurm':
                mount_folder = '/lustre/scratch/sources/physmach/gubaidulin/bii_tracking:/home/dockeruser/bii_tracking'
                slurm_image_name = '/lustre/scratch/sources/physmach/gubaidulin/pycompletecuda.sif'
                # These module commands may fail on non-HPC systems; suppress errors
                try:
                    subprocess.run(['module', 'load', 'singularity'], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass  # Module command not available or failed
                try:
                    subprocess.run(['module', 'load', 'cuda'], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass  # Module command not available or failed

                f.write(f"#SBATCH --partition {job.partition}\n")
                f.write(f"#SBATCH -n {job.n_cpu}\n")
                f.write("#SBATCH -N 1\n")
                f.write(f"#SBATCH --time={job.time}\n")
                f.write('#SBATCH --export=ALL\n')
                if job.is_gpu:
                    f.write('#SBATCH --gres=gpu:1\n')
                f.write("#SBATCH --mail-user='vadim.gubaidulin@synchrotron-soleil.fr'\n")
                f.write('#SBATCH --mail-type=begin,end,requeue\n')
                f.write(f"#SBATCH --error={job.err_folder}{job.name}.err\n")
                f.write(f"#SBATCH --output={job.out_folder}{job.name}.out\n")
                f.write('module load tools/singularity/current\n')
                f.write(
                    f"singularity exec --no-home --nv -B {mount_folder} {slurm_image_name} "
                    + command_string)

        return job.name

    def submit(self, job: Job, cleanup: bool = True) -> None:
        """Submit a job to the cluster.

        Args:
            job: Job configuration object.
            cleanup: Whether to remove the generated script after submission.
        """
        config_file = job.config_file if job.config_file else "config.toml"
        script_name = self._write_submission_script(job, config_file)

        try:
            if self.server == 'ccrt':
                print(f"Submitting job '{job.name}' to CCRT...")
                result = subprocess.run(['ccc_msub', script_name], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Warning: ccc_msub returned non-zero exit code: {result.returncode}")
                    if result.stderr:
                        print(f"Error output: {result.stderr}")
            elif self.server == 'slurm':
                print(f"Submitting job '{job.name}' to SLURM...")
                result = subprocess.run(['sbatch', script_name], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Warning: sbatch returned non-zero exit code: {result.returncode}")
                    if result.stderr:
                        print(f"Error output: {result.stderr}")
            elif self.server == 'local':
                print(f"Local mode: job script '{job.name}' created but not submitted.")
            else:
                print(f"Unknown server type: {self.server}")
        except FileNotFoundError as e:
            print(f"Error: Submission command not found: {e}")

        if cleanup and os.path.exists(script_name):
            os.remove(script_name)


def submit(config_file: str, cleanup: bool = True) -> None:
    """Convenience function to submit a single job from a config file.

    Args:
        config_file: Path to the .toml configuration file.
        cleanup: Whether to remove the generated script after submission.
    """
    job = Job.from_toml(config_file)
    submitter = Submitter(server=job.server)
    submitter.submit(job, cleanup=cleanup)
