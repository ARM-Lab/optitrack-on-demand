"""Run the original one-body, one-CSV-per-Enter experiment."""
from acquire import run_experiment
from config import EXPERIMENT

if __name__ == '__main__':
    run_experiment('single', (EXPERIMENT.single_rigid_body_id,))
