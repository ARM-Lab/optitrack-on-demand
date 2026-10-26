"""Capture three rigid bodies together from the same OptiTrack frame."""
from acquire import run_experiment
from config import EXPERIMENT

if __name__ == '__main__':
    run_experiment('three', EXPERIMENT.three_rigid_body_ids)
