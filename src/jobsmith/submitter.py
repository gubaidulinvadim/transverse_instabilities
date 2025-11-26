"""
Submitter classes for different HPC systems.
"""

import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

from .job import Job


class Submitter(ABC):
    """Abstract base class for job submitters."""
    
    @abstractmethod
    def submit(self, job: Job, cleanup: bool = True) -> Optional[str]:
        """
        Submit a job to the HPC system.
        
        Args:
            job: Job configuration
            cleanup: Whether to clean up temporary files after submission
            
        Returns:
            Job ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def generate_script(self, job: Job) -> str:
        """
        Generate the submission script content.
        
        Args:
            job: Job configuration
            
        Returns:
            Script content as a string
        """
        pass
    
    def write_script(self, job: Job, path: Optional[str] = None) -> str:
        """
        Write the submission script to a file.
        
        Args:
            job: Job configuration
            path: Path to write the script (optional, creates temp file if not provided)
            
        Returns:
            Path to the written script
        """
        content = self.generate_script(job)
        if path is None:
            fd, path = tempfile.mkstemp(suffix='.sh', prefix=f'{job.name}_')
            os.close(fd)
        with open(path, 'w') as f:
            f.write(content)
        return path


class CCRTSubmitter(Submitter):
    """Submitter for CCRT (CEA) HPC system using ccc_msub."""
    
    def __init__(self, home_dir: str = "/ccc/cont003/home/soleil/gubaiduv"):
        """
        Initialize CCRT submitter.
        
        Args:
            home_dir: Home directory for output files
        """
        self.home_dir = home_dir
    
    def generate_script(self, job: Job) -> str:
        """Generate a CCRT submission script."""
        lines = ["#!/bin/bash"]
        lines.append("#MSUB -m work,scratch")
        
        # Queue selection based on time limit
        if job.time_limit >= 86400:
            lines.append("#MSUB -Q long")
        elif job.time_limit <= 1800:
            lines.append("#MSUB -Q test")
        else:
            lines.append("#MSUB -Q normal")
        
        # Partition
        partition = job.partition or "milan"
        lines.append(f"#MSUB -q {partition}")
        
        # Resources
        lines.append(f"#MSUB -n {job.n_tasks}")
        lines.append(f"#MSUB -c {job.n_cpus_per_task}")
        lines.append(f"#MSUB -T {job.time_limit}")
        
        # Account
        account = job.account or "soleil"
        lines.append(f"#MSUB -A {account}")
        
        # Output files
        output_file = job.output_file or f"{self.home_dir}/{job.name}.out"
        error_file = job.error_file or f"{self.home_dir}/{job.name}.err"
        lines.append(f"#MSUB -o {output_file}")
        lines.append(f"#MSUB -e {error_file}")
        
        # Extra args
        for key, value in job.extra_args.items():
            lines.append(f"#MSUB {key} {value}")
        
        # Modules
        lines.append("module purge")
        for module in job.modules:
            lines.append(f"module load {module}")
        
        # Environment variables
        for key, value in job.environment.items():
            lines.append(f"export {key}={value}")
        
        # Command execution
        if job.image:
            # Container execution with ccc_mprun
            mount_args = ":".join([
                f"src={src},dst={dst}" for src, dst in job.mounts.items()
            ])
            container_modules = job.extra_args.get('ctr_module', 'openmpi-4.1.4')
            cmd = (
                f"ccc_mprun -C {job.image} "
                f"-E'--ctr-module {container_modules}' "
            )
            if mount_args:
                cmd += f"-E'--ctr-mount {mount_args}' "
            cmd += f"-- {job.command}"
            lines.append(cmd)
        else:
            lines.append(job.command or f"bash {job.script}")
        
        return "\n".join(lines) + "\n"
    
    def submit(self, job: Job, cleanup: bool = True) -> Optional[str]:
        """Submit a job to CCRT using ccc_msub."""
        script_path = self.write_script(job)
        try:
            result = subprocess.run(
                ["ccc_msub", script_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse job ID from output
                return result.stdout.strip()
            else:
                print(f"Submission failed: {result.stderr}")
                return None
        finally:
            if cleanup:
                os.remove(script_path)


class SLURMSubmitter(Submitter):
    """Submitter for SLURM HPC systems."""
    
    def __init__(self, error_dir: str = "/home/sources/physmach/gubaidulin/err"):
        """
        Initialize SLURM submitter.
        
        Args:
            error_dir: Directory for error files
        """
        self.error_dir = error_dir
    
    def generate_script(self, job: Job) -> str:
        """Generate a SLURM submission script."""
        lines = ["#!/bin/bash"]
        
        # Partition
        partition = job.partition or "sumo"
        lines.append(f"#SBATCH --partition {partition}")
        
        # QOS for long jobs
        if job.time_limit >= 86400:
            lines.append("#SBATCH --qos long")
        
        # Resources
        lines.append(f"#SBATCH -n {job.n_tasks}")
        lines.append(f"#SBATCH --time={job.time_limit}")
        lines.append("#SBATCH --export=ALL")
        
        # Email notifications
        lines.append("#SBATCH --mail-type=begin,end,requeue")
        
        # Error file
        error_file = job.error_file or f"{self.error_dir}/{job.name}_%I.err"
        lines.append(f"#SBATCH --error={error_file}")
        
        # Extra args
        for key, value in job.extra_args.items():
            lines.append(f"#SBATCH {key} {value}")
        
        # Modules
        for module in job.modules:
            lines.append(f"module load {module}")
        
        # Environment variables
        for key, value in job.environment.items():
            lines.append(f"export {key}={value}")
        
        # Command execution
        if job.image:
            # Singularity container execution
            mount_args = ",".join([
                f"{src}:{dst}" for src, dst in job.mounts.items()
            ])
            cmd = f"singularity exec --no-home"
            if mount_args:
                cmd += f" --B {mount_args}"
            cmd += f" {job.image} {job.command}"
            lines.append(cmd)
        else:
            lines.append(job.command or f"bash {job.script}")
        
        return "\n".join(lines) + "\n"
    
    def submit(self, job: Job, cleanup: bool = True) -> Optional[str]:
        """Submit a job to SLURM using sbatch."""
        script_path = self.write_script(job)
        try:
            result = subprocess.run(
                ["sbatch", script_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse job ID from output (e.g., "Submitted batch job 12345")
                parts = result.stdout.strip().split()
                return parts[-1] if parts else None
            else:
                print(f"Submission failed: {result.stderr}")
                return None
        finally:
            if cleanup:
                os.remove(script_path)


def get_submitter(mode: str) -> Submitter:
    """
    Get the appropriate submitter for the given mode.
    
    Args:
        mode: Submission mode ('ccrt' or 'slurm')
        
    Returns:
        Submitter instance
    """
    if mode == "ccrt":
        return CCRTSubmitter()
    elif mode == "slurm":
        return SLURMSubmitter()
    else:
        raise ValueError(f"Unknown submission mode: {mode}")
