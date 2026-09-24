import unittest

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RtspSourceTest(unittest.TestCase):
    def test_set_video_source_accepts_mobile_rtsp_url(self):
        spec = importlib.util.spec_from_file_location('tric_run', ROOT / 'run_tric.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        updated = module.set_video_source('rtsp://user:pass@192.168.1.15:8554/live')
        self.assertEqual(updated, 'rtsp://user:pass@192.168.1.15:8554/live')
        self.assertEqual(module.resolve_video_source(), updated)


if __name__ == '__main__':
    unittest.main()
