# OptiTrack on-demand rigid-body acquisition

A Python application for manually saving rigid-body measurements streamed from **OptiTrack Motive** via **NatNet**. Press **Enter** to save the latest received tracking frame; type **q** and press Enter to quit.

Two experiments are supported:

| Experiment | Run | Data saved per keypress |
| --- | --- | --- |
| Single rigid body | `python single_body.py` | One CSV containing one rigid body |
| Three rigid bodies | `python three_bodies.py` | One CSV containing three rigid bodies from the **same NatNet frame** |

Each rigid body has a 3D position, an orientation quaternion and up to three marker positions. Files are generated only when the operator requests a capture; **this is not continuous trajectory recording**.

## 1. Prerequisites

- A running **OptiTrack Motive** installation, with calibrated cameras, the required rigid bodies configured and NatNet streaming enabled.
- A computer able to receive NatNet data from the Motive machine (this may be the same computer if configured accordingly).
- **Python 3.10 or later** (the project uses modern type annotations; using the same Python version as the original acquisition PC is preferable).
- **Git**, used both to clone this project and to install the pinned NatNet Python client.

The original working environment used the NatNet client from [`TimSchneider42/python-natnet-client`](https://github.com/TimSchneider42/python-natnet-client), pinned to commit `f65eb186d5275be997cdb7ec2ac5989062070c8e`. Python packages with similar NatNet names can have **different APIs**; do not substitute another client without adapting the code.

## 2. Install the project

Open a terminal on the computer that will run Python.

```bash
git clone https://github.com/ARM-Lab/optitrack-on-demand.git
cd optitrack-on-demand
python -m venv .venv
```

Activate the environment:

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```bat
.venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify the NatNet import:

```bash
python -c "from natnet import NatNetClient; print(NatNetClient)"
```

**Important:** This checks only that the import succeeds, not that the client is compatible with the acquisition code or that Motive can be reached. Confirm the complete acquisition workflow on the actual system before recording experimental results.

## 3. Configure OptiTrack Motive

1. Calibrate the tracking volume and confirm rigid-body tracking in Motive.
2. Define and name the rigid bodies that will be measured.
3. Find their **rigid-body IDs** in Motive / the NatNet model definitions. The names and IDs are different properties; this application selects bodies by **ID**.
4. Enable NatNet streaming in Motive, and record the Motive computer's IP address.
5. Ensure the Python computer is on a reachable network and firewall rules permit the NatNet connection and data traffic. Match the multicast setting used in Motive.

In the project root, open **`config.py`** and change the settings to match the equipment:

```python
@dataclass(frozen=True)
class NatNetConfig:
    server_ip_address: str = "192.168.1.61"  # IP of Motive computer
    local_ip_address: str = "192.168.1.12"   # IP of Python computer
    use_multicast: bool = True

@dataclass(frozen=True)
class ExperimentConfig:
    output_dir: Path = Path("runs")
    poll_interval_s: float = 0.005
    single_rigid_body_id: int = 3
    three_rigid_body_ids: tuple[int, int, int] = (3, 4, 5)
    marker_set_names: dict[int, str] | None = None
    max_frame_age_s: float = 0.5
```

The shown IP addresses and three-body IDs are **examples, not universal values**. Replace them as required.

**Marker sets:** The application reads markers from `frame.marker_sets` and associates a marker set with each rigid body by name. By default, the expected marker-set name equals the rigid-body name advertised by Motive. If those names differ, set an explicit mapping, for example:

```python
marker_set_names: dict[int, str] | None = {
    3: "RigidBody2",
    4: "RigidBody4",
    5: "RigidBody5",
}
```

Check the actual marker-set names on your installation; the example names may not exist. Missing or mismatched marker sets will result in **blank marker fields**, even if the rigid-body pose is available.

## 4. Run the acquisition

### Experiment A — single rigid body

```bash
python single_body.py
```

The script connects to Motive and receives frames in the background. On each **Enter** keypress, it checks the latest received frame and saves one CSV containing the configured rigid body's information.

### Experiment B — three rigid bodies

First set all three IDs in `three_rigid_body_ids` in `config.py`:

```python
three_rigid_body_ids: tuple[int, int, int] = (3, 4, 5)
```

Then start:

```bash
python three_bodies.py
```

Each **Enter** keypress saves one CSV with **three rows**, one for each configured body. All three samples come from the **same received NatNet frame**. If any required rigid body is missing or marked as not tracked, the entire capture is skipped rather than combining measurements from different frames.

**Keyboard controls (both modes):**

| Input | Action |
| --- | --- |
| `Enter` | Save latest valid frame to a new CSV file |
| `q` then `Enter` | Quit gracefully |
| `Ctrl+C` | Interrupt the program |

Both modes skip frames older than `max_frame_age_s` (default 0.5 s). An Enter keypress selects the **most recently received frame**, not a newly triggered camera exposure at the exact keypress time.

## 5. Saved measurements

The program creates a new timestamped session folder under `runs/` each time it starts:

```text
runs/
  single_2026-10-26_11-00-00/
    capture_0001_2026-10-26_11-00-12_123456.csv
    capture_0002_2026-10-26_11-00-18_234567.csv
  three_2026-10-26_11-15-00/
    capture_0001_2026-10-26_11-15-10_345678.csv
```

Each CSV has the same header:

```csv
timestamp,rigid_body_name,x,y,z,m1x,m1y,m1z,m2x,m2y,m2z,m3x,m3y,m3z,qx,qy,qz,qw
```

| Column(s) | Meaning |
| --- | --- |
| `timestamp` | Unix timestamp (seconds) from the **Python PC's local receive clock**; not Motive's precise camera/frame timestamp |
| `rigid_body_name` | Rigid-body name from the NatNet model description, or a fallback such as `rb_3` |
| `x, y, z` | Rigid-body position in **metres** |
| `m1x`–`m3z` | Positions of up to three markers associated with the body, in **metres** |
| `qx, qy, qz, qw` | Rigid-body orientation quaternion in NatNet's reported component order |

Example layout for **three-body mode** (illustrative, not real measurements):

```csv
timestamp,rigid_body_name,x,y,z,m1x,m1y,m1z,m2x,m2y,m2z,m3x,m3y,m3z,qx,qy,qz,qw
1793010000.1,BodyA,0.1,0.2,0.3,,,,,,,,,,0,0,0,1
1793010000.1,BodyB,0.4,0.5,0.6,,,,,,,,,,0,0,0,1
1793010000.1,BodyC,0.7,0.8,0.9,,,,,,,,,,0,0,0,1
```

The blank marker fields in this illustration are placeholders. In actual experiments, marker positions are recorded when a matching marker set and markers are present.

The script **does not transform coordinates** or convert orientations to Euler angles. Values are exported in the coordinate system and representation provided by the NatNet client.

## 6. Repository files

| File | Purpose |
| --- | --- |
| `single_body.py` | Entry point for the original single-body capture |
| `three_bodies.py` | Entry point for the three-body capture |
| `config.py` | Connection settings, rigid-body IDs, marker mapping and capture parameters |
| `tracker.py` | NatNet connection, model descriptions and latest-frame snapshot |
| `acquire.py` | Keyboard loop, capture validation and session organisation |
| `logger.py` | CSV output format and file writing |
| `experiment_types.py` | Structure of one rigid-body measurement |
| `requirements.txt` | Pinned NatNet Python dependency |
| `tests/test_offline.py` | Offline checks that do not require Motive |

## 7. Common problems

- **Cannot connect / no frame arrives:** Verify Motive streaming, IP addresses, multicast/unicast configuration, firewall and network connectivity.
- **`ModuleNotFoundError: natnet`:** Activate the correct virtual environment and run `python -m pip install -r requirements.txt`.
- **Import succeeds but the program raises `AttributeError` or a NatNet callback error:** The installed client/API may not match the code. Verify the pinned commit and compare with the working acquisition computer.
- **Capture skipped, missing rigid-body IDs:** Check the IDs configured in `config.py`, confirm all required bodies are visible and tracked, and restart after changing the Motive model definitions.
- **Positions recorded but marker columns are empty:** Check `marker_set_names` and confirm Motive streams the expected markers. Also verify the marker-set data structure is supported by the client.
- **Wrong marker assigned to m1/m2/m3:** Marker-set array order may not be stable physical marker identity. Validate marker correspondence separately if your analysis relies on it.

## 8. Validation and reproducibility

Before relying on the data, perform a simple test: place each body at a known location, verify its exported coordinates, rotate it to verify quaternion conventions, and inspect all three marker positions. For the three-body experiment, temporarily occlude one rigid body and confirm the capture is rejected.

This repository's refactored acquisition code has **not yet been verified with a live Motive system**. Its offline tests do not prove end-to-end compatibility with the installed NatNet client. Run hardware validation before collecting research measurements.

Experimental captures under `runs/` are excluded from Git by `.gitignore`.
