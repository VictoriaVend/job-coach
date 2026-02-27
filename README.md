# My Project

## Setup

python -m venv venv
.\venv\Scripts\activate
pip install -U pip
pip install .[dev]
pip install pre-commit
pre-commit install
pre-commit run --all-files
## Run

python -m job_coach.main