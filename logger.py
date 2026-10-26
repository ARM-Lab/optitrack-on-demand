"""One CSV per keypress, one row per rigid body."""
import csv
from dataclasses import asdict
from pathlib import Path
from experiment_types import MocapSample

FIELDNAMES = ['timestamp', 'rigid_body_name', 'x', 'y', 'z',
              'm1x', 'm1y', 'm1z', 'm2x', 'm2y', 'm2z', 'm3x', 'm3y', 'm3z',
              'qx', 'qy', 'qz', 'qw']

def save_capture(path: Path, samples: list[MocapSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for sample in samples:
            writer.writerow(asdict(sample))
