"""
Parameter scan utilities for submitting multiple jobs.
"""

from itertools import product
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from .job import Job
from .submitter import Submitter, get_submitter


class ParameterGrid:
    """
    A class for generating parameter combinations for scans.
    
    Example:
        >>> grid = ParameterGrid({
        ...     'bunch_current': [1e-3, 2e-3, 3e-3],
        ...     'chromaticity': [0.0, 1.6],
        ... })
        >>> for params in grid:
        ...     print(params)
    """
    
    def __init__(self, param_dict: Dict[str, List[Any]]):
        """
        Initialize parameter grid.
        
        Args:
            param_dict: Dictionary mapping parameter names to lists of values
        """
        self.param_dict = param_dict
        self._keys = list(param_dict.keys())
        self._values = [param_dict[k] for k in self._keys]
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over all parameter combinations."""
        for combo in product(*self._values):
            yield dict(zip(self._keys, combo))
    
    def __len__(self) -> int:
        """Return the total number of parameter combinations."""
        result = 1
        for values in self._values:
            result *= len(values)
        return result


def submit_scan(
    submitter: Union[str, Submitter],
    param_grid: Union[Dict[str, List[Any]], ParameterGrid],
    job_factory: Callable[[Dict[str, Any]], Job],
    dry_run: bool = False,
) -> List[Optional[str]]:
    """
    Submit a parameter scan to an HPC system.
    
    This function generates and submits jobs for all combinations of parameters
    in the parameter grid.
    
    Args:
        submitter: Submitter instance or mode string ('ccrt', 'slurm')
        param_grid: Parameter grid as a dict or ParameterGrid instance
        job_factory: Function that takes parameter dict and returns a Job
        dry_run: If True, print jobs without submitting
        
    Returns:
        List of job IDs (or None for failed submissions)
        
    Example:
        >>> def make_job(params):
        ...     return Job(
        ...         name=f"scan_{params['current']:.1e}",
        ...         command=f"python track.py --current {params['current']}",
        ...         time_limit=86000,
        ...     )
        >>> 
        >>> job_ids = submit_scan(
        ...     'ccrt',
        ...     {'current': [1e-3, 2e-3, 3e-3]},
        ...     make_job,
        ... )
    """
    if isinstance(submitter, str):
        submitter = get_submitter(submitter)
    
    if isinstance(param_grid, dict):
        param_grid = ParameterGrid(param_grid)
    
    job_ids = []
    for params in param_grid:
        job = job_factory(params)
        if dry_run:
            print(f"Would submit: {job.name}")
            print(f"  Parameters: {params}")
            print(f"  Command: {job.command}")
            job_ids.append(None)
        else:
            try:
                job_id = submitter.submit(job)
                job_ids.append(job_id)
                print(f"Submitted {job.name}: {job_id}")
            except Exception as e:
                print(f"Failed to submit {job.name}: {e}")
                job_ids.append(None)
    
    return job_ids
