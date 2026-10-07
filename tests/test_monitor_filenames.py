import tempfile
import unittest
from pathlib import Path

from src.monitor_filenames import get_monitor_filename


class GetMonitorFilenameTest(unittest.TestCase):

    def test_single_bunch_filename_matches_tracking_format(self):
        filename = get_monitor_filename(
            {
                "folder": "/data/",
                "n_turns": 50_000,
                "n_macroparticles": 500_000,
                "n_bin": 100,
                "bunch_current": 1.2e-3,
                "Qp_x": 0.0,
                "Qp_y": 0.0,
                "id_state": "close",
                "include_Zlong": True,
                "harmonic_cavity": False,
                "feedback_tau": 0,
                "feedback_phase": -75,
                "sc": True,
                "ibs": True,
                "wake_types": ["Wydip", "Wxdip"],
                "emittance_ratio": 1.0,
                "emittance_control_method": "skew_quadrupole",
                "skew_strength": 0.001,
            },
            tracking_script="track_TI.py",
        )

        self.assertEqual(
            filename,
            "/data/mon(nmp=5.0e+05,nt=5.0e+04,nb=100,I=1.20e-03,"
            "Qpx=0.00,Qpy=0.00,id=close,Zl=True,HC=False,fb_tau=0.0e+00,"
            "phi=-75,sc=True,ibs=True,wakes=Wydip-Wxdip,"
            "emit_ctrl=skew_quadrupole,"
            "er=1.0,base_er=0.020,skew_k=1.00e-03,skew_qx=54.200,"
            "skew_qy=18.200)",
        )

    def test_multi_bunch_filename_uses_configured_fill_pattern(self):
        filename = get_monitor_filename(
            {
                "folder": "/data/",
                "n_turns": 30_000,
                "n_macroparticles": 100_000,
                "bunch_current": 0.00625,
                "fill_pattern": "uniform",
                "n_bunches": 32,
                "wake_types": ["Wxdip", "Wxquad"],
            },
            tracking_script="track_mb.py",
            harmonic_number=416,
        )

        self.assertEqual(
            filename,
            "/data/monitors(n_mp=1.0e+05,n_turns=3.0e+04,n_bin=100,"
            "bunch_current=6.3e-03,n_bunches=32,fill_pattern=uniform,"
            "Qp_x=1.80,Qp_y=1.40,ID_state=open,include_Zlong=False,"
            "harmonic_cavity=False,feedback_tau=1.0e+02,"
            "phi=-90,sc=False,ibs=False,"
            "wake_types=Wxdip-Wxquad)",
        )

    def test_toml_path_infers_script_and_can_include_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                """
[script]
name = "/workspace/src/simulation/track_TI.py"
folder = "/data/"
n_turns = 1000
""",
                encoding="utf-8",
            )

            filename = get_monitor_filename(
                config_path,
                include_extension=True,
            )

        self.assertTrue(filename.startswith("/data/mon("))
        self.assertTrue(filename.endswith(".hdf5"))


if __name__ == "__main__":
    unittest.main()
