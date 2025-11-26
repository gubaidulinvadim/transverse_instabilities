"""
Job class for representing HPC job configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Job:
    """
    Represents a job to be submitted to an HPC cluster.
    
    Attributes:
        name: Job name
        script: Path to the script to execute
        command: Command to run (alternative to script)
        time_limit: Time limit in seconds
        n_tasks: Number of tasks/processes
        n_cpus_per_task: Number of CPUs per task
        memory: Memory allocation (e.g., '4G')
        partition: Queue/partition name
        image: Container image name (for containerized execution)
        mounts: Volume mounts for containers
        modules: Modules to load before execution
        environment: Environment variables
        output_file: Path for stdout
        error_file: Path for stderr
        account: Account/project to charge
        extra_args: Additional scheduler-specific arguments
    """
    name: str
    script: Optional[str] = None
    command: Optional[str] = None
    time_limit: int = 86400  # 24 hours default
    n_tasks: int = 1
    n_cpus_per_task: int = 1
    memory: Optional[str] = None
    partition: Optional[str] = None
    image: Optional[str] = None
    mounts: Dict[str, str] = field(default_factory=dict)
    modules: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    output_file: Optional[str] = None
    error_file: Optional[str] = None
    account: Optional[str] = None
    extra_args: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.script is None and self.command is None:
            raise ValueError("Either 'script' or 'command' must be provided")

    def to_dict(self) -> Dict[str, Any]:
        """Convert job configuration to a dictionary."""
        return {
            'name': self.name,
            'script': self.script,
            'command': self.command,
            'time_limit': self.time_limit,
            'n_tasks': self.n_tasks,
            'n_cpus_per_task': self.n_cpus_per_task,
            'memory': self.memory,
            'partition': self.partition,
            'image': self.image,
            'mounts': self.mounts,
            'modules': self.modules,
            'environment': self.environment,
            'output_file': self.output_file,
            'error_file': self.error_file,
            'account': self.account,
            'extra_args': self.extra_args,
        }
