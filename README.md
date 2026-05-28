# mbtrack2_transverse_instabilities

Simulation tools for tracking transverse beam instabilities using mbtrack2.

## Overview

This repository provides simulation scripts for studying transverse instabilities in synchrotron light sources, including:

- **Single-bunch instabilities** (TMCI, head-tail modes)
- **Multi-bunch instabilities** (coupled-bunch instabilities)

The simulations use the [mbtrack2](https://github.com/lnls-fac/mbtrack2) tracking library.

## Installation

```bash
# Clone the repository
git clone https://github.com/gubaidulinvadim/mbtrack2_transverse_instabilities.git
cd mbtrack2_transverse_instabilities

# Ensure Python path includes the src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Dependencies

- numpy
- mbtrack2
- facilities_mbtrack2 (for SOLEIL II parameters)
- tqdm

## Usage

### Running Simulations Locally

#### Single-Bunch Tracking

```bash
cd src/simulation
python track_TI.py --n_macroparticles 500000 \
                   --n_turns 50000 \
                   --bunch_current 1.2e-3 \
                   --Qp_x 1.6 \
                   --Qp_y 1.6 \
                   --id_state close
```

#### Multi-Bunch Tracking

```bash
cd src/simulation
python track_mb.py --n_macroparticles 100000 \
                   --n_turns 100000 \
                   --bunch_current 1.2e-3 \
                   --n_turns_wake 50
```

### Job Submission with jobsmith

For submitting jobs to HPC systems, use the `jobsmith` module:

#### Single Job Submission

```python
from jobsmith import Job, CCRTSubmitter

# Create a job
job = Job(
    name="tmci_1.2mA",
    command="/home/dockeruser/venv/bin/python3 /home/dockeruser/transverse_instabilities/src/simulation/track_TI.py --bunch_current 1.2e-3 --n_turns 50000",
    time_limit=85000,
    n_tasks=1,
    n_cpus_per_task=8,
    image="soleil-pa:mbtrack2",
    modules=["mpi/openmpi/4.1.4"],
    mounts={
        "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/": "/home/dockeruser/transverse_instabilities/src/",
        "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/": "/home/dockeruser/facilities_mbtrack2/",
        "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/": "/home/dockeruser/transverse_instabilities/data/",
    },
)

# Submit to CCRT
submitter = CCRTSubmitter()
job_id = submitter.submit(job)
print(f"Submitted job: {job_id}")
```

#### Parameter Scans

```python
import numpy as np
from jobsmith import Job, submit_scan, ParameterGrid

def make_single_bunch_job(params):
    """Create a single-bunch tracking job from scan parameters."""
    return Job(
        name=f"tmci_{params['bunch_current']:.1e}_Qp={params['chromaticity']:.1f}",
        command=(
            f"/home/dockeruser/venv/bin/python3 "
            f"/home/dockeruser/transverse_instabilities/src/simulation/track_TI.py "
            f"--bunch_current {params['bunch_current']} "
            f"--Qp_x {params['chromaticity']} "
            f"--Qp_y {params['chromaticity']} "
            f"--n_turns {params.get('n_turns', 50000)} "
            f"--n_macroparticles {params.get('n_macroparticles', 500000)}"
        ),
        time_limit=85000,
        n_tasks=1,
        n_cpus_per_task=8,
        image="soleil-pa:mbtrack2",
        modules=["mpi/openmpi/4.1.4"],
        mounts={
            "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/": "/home/dockeruser/transverse_instabilities/src/",
            "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/": "/home/dockeruser/facilities_mbtrack2/",
            "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/": "/home/dockeruser/transverse_instabilities/data/",
        },
    )

# Define parameter grid
param_grid = ParameterGrid({
    'bunch_current': np.linspace(0.2e-3, 6e-3, 30),
    'chromaticity': [0.0, 1.6],
})

# Submit all jobs (use dry_run=True to preview without submitting)
job_ids = submit_scan('ccrt', param_grid, make_single_bunch_job, dry_run=False)
```

#### Multi-Bunch Scans

```python
from jobsmith import Job, submit_scan, ParameterGrid

def make_multibunch_job(params):
    """Create a multi-bunch tracking job from scan parameters."""
    return Job(
        name=f"tcbi_Qp={params['chromaticity']:.1f}_{params['bunch_current']:.1e}",
        command=(
            f"/home/dockeruser/venv/bin/python3 -u "
            f"/home/dockeruser/transverse_instabilities/src/simulation/track_mb.py "
            f"--bunch_current {params['bunch_current']} "
            f"--Qp_x {params['chromaticity']} "
            f"--Qp_y {params['chromaticity']} "
            f"--n_turns_wake {params.get('n_turns_wake', 50)}"
        ),
        time_limit=86000,
        n_tasks=416,
        n_cpus_per_task=1,
        image="soleil-pa:mbtrack2",
        modules=["mpi/openmpi/4.1.4"],
        mounts={
            "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/": "/home/dockeruser/transverse_instabilities/src/",
            "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/": "/home/dockeruser/facilities_mbtrack2/",
            "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/": "/home/dockeruser/transverse_instabilities/data/",
        },
    )

# Submit multi-bunch scan
param_grid = ParameterGrid({
    'bunch_current': [1.2e-3],
    'chromaticity': np.linspace(0.2, 3.0, 15),
})

job_ids = submit_scan('ccrt', param_grid, make_multibunch_job)
```

### CLI Usage

You can also submit jobs directly via the command line (deprecated, use Python API instead):

```bash
cd src/submission
python submission.py --sub_mode ccrt \
                     --job_name my_job \
                     --job_time 85000 \
                     --bunch_current 1.2e-3
```

## Simulation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_macroparticles` | Number of macroparticles per bunch | 1,000,000 |
| `n_turns` | Number of tracking turns | 50,000 |
| `n_bin` | Number of bins for wakefield | 100 |
| `bunch_current` | Single-bunch current (A) | 1.2e-3 |
| `Qp_x`, `Qp_y` | Chromaticity | 1.6 |
| `id_state` | Insertion device state (`open`/`close`) | `open` |
| `include_Zlong` | Include longitudinal impedance | `False` |
| `harmonic_cavity` | Enable harmonic cavity | `False` |
| `max_kick` | Maximum feedback kick (rad) | 1.6e-6 |
| `sc` | Include space charge | `False` |
| `ibs` | Include intrabeam scattering | `False` |
| `quad` | Include quadrupolar wake | `False` |
| `wake_y` | Track vertical wake (vs horizontal) | `True` |
| `n_turns_wake` | Turns for long-range wake (multi-bunch) | 1 |

## Migration from submission/ to jobsmith

The `submission/` folder is deprecated and will be removed in a future release.
Please migrate your scripts to use `jobsmith` instead.

### Before (deprecated):

```python
# Using submission/submission.py
import os
from submission.submission import write_submission_script

job = write_submission_script(
    sub_mode='ccrt',
    job_name='my_job',
    job_time='85000',
    bunch_current=1.2e-3,
)
os.system(f"ccc_msub {job}")
```

### After (recommended):

```python
from jobsmith import Job, CCRTSubmitter

job = Job(
    name='my_job',
    command='python track_TI.py --bunch_current 1.2e-3',
    time_limit=85000,
    image='soleil-pa:mbtrack2',
)
submitter = CCRTSubmitter()
submitter.submit(job)
```

## Project Structure

```
mbtrack2_transverse_instabilities/
├── README.md
├── src/
│   ├── jobsmith/           # Job submission library
│   │   ├── __init__.py
│   │   ├── job.py          # Job configuration class
│   │   ├── submitter.py    # CCRT/SLURM submitters
│   │   └── scan.py         # Parameter scan utilities
│   ├── simulation/         # Tracking scripts
│   │   ├── track_TI.py     # Single-bunch tracking
│   │   ├── track_mb.py     # Multi-bunch tracking
│   │   ├── setup_tracking.py
│   │   └── utils.py
│   ├── submission/         # [DEPRECATED] Old submission scripts
│   └── postprocessing/     # Data analysis utilities
```

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
