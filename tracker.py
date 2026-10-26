"""Read a coherent snapshot of selected rigid bodies from ONE NatNet frame."""
from __future__ import annotations
from dataclasses import dataclass
import threading
import time
from natnet import NatNetClient
from experiment_types import MocapSample

@dataclass(frozen=True)
class Snapshot:
    received_monotonic_s: float
    samples: dict[int, MocapSample]

class NatNetTracker:
    def __init__(self, *, server_ip_address: str, local_ip_address: str,
                 use_multicast: bool, rigid_body_ids: tuple[int, ...],
                 marker_set_names: dict[int, str] | None = None) -> None:
        if not rigid_body_ids or len(set(rigid_body_ids)) != len(rigid_body_ids):
            raise ValueError("Rigid-body IDs must be unique and non-empty")
        self.ids = rigid_body_ids
        self._marker_set_names = marker_set_names or {}
        self._lock = threading.Lock()
        self._names: dict[int, str] = {}
        self._latest: Snapshot | None = None
        self._client = NatNetClient(server_ip_address=server_ip_address,
                                    local_ip_address=local_ip_address,
                                    use_multicast=use_multicast)
        self._client.on_data_description_received_event.handlers.append(self._on_description)
        self._client.on_data_frame_received_event.handlers.append(self._on_frame)

    def _on_description(self, desc) -> None:
        names = {}
        for rb in getattr(desc, 'rigid_bodies', ()) or ():
            rb_id = getattr(rb, 'id_num', None)
            if rb_id is not None:
                names[rb_id] = getattr(rb, 'name', None) or f'rb_{rb_id}'
        with self._lock:
            self._names = names
        print('Rigid bodies advertised by Motive:', names)

    @staticmethod
    def _triplet(markers, index):
        return tuple(map(float, markers[index])) if index < len(markers) else (None, None, None)

    def _on_frame(self, frame) -> None:
        with self._lock:
            names = dict(self._names)
        sets = {getattr(ms, 'model_name', None): ms for ms in
                (getattr(frame, 'marker_sets', ()) or ())}
        samples: dict[int, MocapSample] = {}
        received_at = time.monotonic()
        frame_timestamp = time.time()  # acquisition-PC receive-time, not Motive frame timestamp
        for rb in getattr(frame, 'rigid_bodies', ()) or ():
            rb_id = getattr(rb, 'id_num', None)
            if rb_id not in self.ids:
                continue
            if not getattr(rb, 'tracking_valid', True):
                continue
            pos, rot = getattr(rb, 'pos', None), getattr(rb, 'rot', None)
            if pos is None or rot is None:
                continue
            name = names.get(rb_id, f'rb_{rb_id}')
            set_name = self._marker_set_names.get(rb_id, name)
            marker_set = sets.get(set_name)
            markers = (getattr(marker_set, 'marker_pos_list', ()) or ()) if marker_set is not None else ()
            m1 = self._triplet(markers, 0)
            m2 = self._triplet(markers, 1)
            m3 = self._triplet(markers, 2)
            samples[rb_id] = MocapSample(
                timestamp=frame_timestamp, rigid_body_name=name,
                x=float(pos[0]), y=float(pos[1]), z=float(pos[2]),
                m1x=m1[0], m1y=m1[1], m1z=m1[2],
                m2x=m2[0], m2y=m2[1], m2z=m2[2],
                m3x=m3[0], m3y=m3[1], m3z=m3[2],
                qx=float(rot[0]), qy=float(rot[1]), qz=float(rot[2]), qw=float(rot[3]))
        # Store even incomplete frames to prevent silently mixing frames.
        with self._lock:
            self._latest = Snapshot(received_monotonic_s=received_at, samples=samples)

    def get_latest_snapshot(self) -> Snapshot | None:
        with self._lock:
            return self._latest

    def connect(self):
        self._client.connect()
        self._client.request_modeldef()

    def update(self):
        self._client.update_sync()

    def shutdown(self):
        self._client.shutdown()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()
