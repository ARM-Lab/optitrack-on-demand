"""Test callback extraction without NatNet hardware or the NatNet package."""
import csv
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

# Stub the third-party dependency before importing the module.
dummy = types.ModuleType('natnet')
class Client:
    def __init__(self, **kwargs):
        self.on_data_description_received_event = NS(handlers=[])
        self.on_data_frame_received_event = NS(handlers=[])
dummy.NatNetClient = Client
sys.modules['natnet'] = dummy
from tracker import NatNetTracker
from logger import save_capture

class TestTracker(unittest.TestCase):
    def test_three_bodies_same_frame_and_csv(self):
        tracker = NatNetTracker(server_ip_address='127.0.0.1', local_ip_address='127.0.0.1',
                                use_multicast=False, rigid_body_ids=(1,2,3))
        tracker._on_description(NS(rigid_bodies=[NS(id_num=i,name=f'RB{i}') for i in (1,2,3)]))
        frame = NS(rigid_bodies=[NS(id_num=i, pos=(i,2,3), rot=(0,0,0,1), tracking_valid=True)
                                 for i in (1,2,3)],
                   marker_sets=[NS(model_name=f'RB{i}',marker_pos_list=[(i,0,0),(i,1,0),(i,2,0)]) for i in (1,2,3)])
        tracker._on_frame(frame)
        snapshot = tracker.get_latest_snapshot()
        self.assertEqual(set(snapshot.samples), {1,2,3})
        self.assertEqual(len({s.timestamp for s in snapshot.samples.values()}), 1)
        self.assertEqual(snapshot.samples[2].m3x, 2.0)
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'sample.csv'
            save_capture(file, list(snapshot.samples.values()))
            with file.open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[0]['rigid_body_name'], 'RB1')

    def test_missing_body_is_not_reused_from_old_frame(self):
        tracker = NatNetTracker(server_ip_address='a',local_ip_address='b',
                                use_multicast=False,rigid_body_ids=(1,2,3))
        def frame(ids):
            return NS(rigid_bodies=[NS(id_num=i,pos=(0,0,0),rot=(0,0,0,1),tracking_valid=True)
                                    for i in ids], marker_sets=[])
        tracker._on_frame(frame((1,2,3)))
        tracker._on_frame(frame((1,3)))
        self.assertEqual(set(tracker.get_latest_snapshot().samples),{1,3})

if __name__ == '__main__':
    unittest.main()
