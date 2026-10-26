"""Shared keyboard acquisition loop for both experiment modes."""
import threading
import time
from datetime import datetime
from pathlib import Path

from config import NATNET, EXPERIMENT
from logger import save_capture
from tracker import NatNetTracker

def _run_tracking(tracker, stop):
    while not stop.is_set():
        tracker.update()
        stop.wait(EXPERIMENT.poll_interval_s)

def run_experiment(mode: str, ids: tuple[int, ...]) -> None:
    session = (EXPERIMENT.output_dir / f'{mode}_{datetime.now():%Y-%m-%d_%H-%M-%S}')
    stop = threading.Event()
    with NatNetTracker(server_ip_address=NATNET.server_ip_address,
                       local_ip_address=NATNET.local_ip_address,
                       use_multicast=NATNET.use_multicast,
                       rigid_body_ids=ids,
                       marker_set_names=EXPERIMENT.marker_set_names) as tracker:
        worker = threading.Thread(target=_run_tracking, args=(tracker, stop), daemon=True)
        worker.start()
        print(f'Mode: {mode}; rigid-body IDs: {ids}')
        print('Press Enter to capture; type q and Enter to quit.')
        print(f'Output directory: {session.resolve()}')
        count = 0
        try:
            while True:
                command = input('Capture [Enter] / Quit [q]: ').strip().lower()
                if command == 'q':
                    break
                snapshot = tracker.get_latest_snapshot()
                if snapshot is None:
                    print('No OptiTrack frame received yet.')
                    continue
                age = time.monotonic() - snapshot.received_monotonic_s
                if age > EXPERIMENT.max_frame_age_s:
                    print(f'Frame too old ({age:.2f} s); capture skipped.')
                    continue
                missing = [rb_id for rb_id in ids if rb_id not in snapshot.samples]
                if missing:
                    print(f'Capture skipped: missing/untracked rigid-body IDs {missing}.')
                    continue
                samples = [snapshot.samples[rb_id] for rb_id in ids]
                count += 1
                path = session / f'capture_{count:04d}_{datetime.now():%Y-%m-%d_%H-%M-%S_%f}.csv'
                save_capture(path, samples)
                print(f'Saved {len(samples)} rigid body(ies): {path.name}')
                for sample in samples:
                    print(f'  {sample.rigid_body_name}: x={sample.x:.4f}, y={sample.y:.4f}, z={sample.z:.4f} m')
        except KeyboardInterrupt:
            print('Stopped by keyboard interrupt.')
        finally:
            stop.set()
            worker.join(timeout=2.0)
