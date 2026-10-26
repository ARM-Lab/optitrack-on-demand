"""Edit these settings before running either acquisition mode."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class NatNetConfig:
    server_ip_address: str = "192.168.1.61"  # Motive PC
    local_ip_address: str = "192.168.1.12"   #  Tvoj PC
    use_multicast: bool = True

@dataclass(frozen=True)
class ExperimentConfig:
    output_dir: Path = Path("runs")
    poll_interval_s: float = 0.005
    # Motive rigid body IDs. Determine IDs in Motive / model definitions.
    single_rigid_body_id: int = 3
    three_rigid_body_ids: tuple[int, int, int] = (3, 4, 5)  # EXAMPLE: CHANGE
    # Marker set names as reported by NatNet; use None to match body name.
    marker_set_names: dict[int, str] | None = None
    # e.g. {3: "RigidBody2", 4: "RigidBody4", 5: "RigidBody5"}
    # If marker set names do not equal Motive rigid-body names, populate above.
    max_frame_age_s: float = 0.5

NATNET = NatNetConfig()
EXPERIMENT = ExperimentConfig()
