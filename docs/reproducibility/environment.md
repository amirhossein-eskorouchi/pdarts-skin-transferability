# Environment policy

## Maintained package environment

The maintained package intentionally uses the Python standard library.

Supported Python versions:

- Python 3.10;
- Python 3.11; and
- Python 3.12.

The repository environment can be created with:

    conda env create -f environment.yml
    conda activate pdarts-skin-maintained

Or with a standard virtual environment:

    python -m venv .venv
    python -m pip install --upgrade pip
    python -m pip install -e .
    python -m pip install -r requirements-dev.txt

## Historical deep-learning environments

The private archive contains evidence from multiple historical environments,
including different PyTorch, CUDA, operating-system, and Python combinations.

Those environments are evidence, not a single resolved reproducibility lock.

The maintained package must not claim that a historical checkpoint or result
can be reproduced merely by installing the lightweight environment above.

## Future experiment runtime

Executing P-DARTS search or evaluation will require a separately approved
deep-learning environment and an authorized upstream implementation.

That future environment must record:

- Python version;
- PyTorch and torchvision versions;
- CUDA runtime;
- GPU model;
- operating system;
- deterministic-algorithm settings;
- cuDNN settings;
- dependency lock;
- dataset versions;
- split-manifest hashes; and
- Git commit.

No GPU-specific dependency is installed by the current continuous-integration
workflow.
