import numpy as np
from mbtrack2.impedance.wakefield import WakeField, WakeFunction
from mbtrack2.tracking import (Bunch, LongitudinalMap, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from tqdm import tqdm
import argparse
import os, sys
from scipy.constants import c

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_toml_config

os.environ["PYTHONPATH"] += os.pathsep + "/home/dockeruser/facilities_mbtrack2/"
sys.path.append('/home/dockeruser/facilities_mbtrack2')
from facilities_mbtrack2.ESRF_EBS import esrf_ebs

def run_mbtrack2(config: dict) -> None:
    folder = config['folder']
    n_turns = config.get('n_turns', 100_000)
    n_macroparticles = config.get('n_macroparticles', int(1e6))
    n_bin = config.get('n_bin', 100)
    bunch_current = config.get('bunch_current', 1e-3)
    Qp_x = config.get('Qp_x', 1.6)
    Qp_y = config.get('Qp_y', 1.6)
    sc = config.get('sc', False)
    emittance_y = config.get('emittance_y', 10e-12)

    Vc = 6e6
    ring = esrf_ebs()
    ring.chro = np.array([Qp_x, Qp_y])
    ring.emit[1] = emittance_y
    mybunch = Bunch(ring,
                    mp_number=n_macroparticles,
                    current=bunch_current,
                    track_alive=False)
    np.random.seed(42)
    mybunch.init_gaussian()
    monitor_filename = folder + f"esrf_monitors(n_mp={n_macroparticles:.1e}," + \
        f"n_turns={n_turns:.1e}," +\
        f"n_bin={n_bin:},"+\
        f"bunch_current={bunch_current:.2e},"+\
        f"Qp_x={Qp_x:.2f},"+\
        f"Qp_y={Qp_y:.2f},"+\
        f"emit_y={emittance_y:.1e}"+\
        f"sc={sc:}"+\
        ")"
    bunch_monitor = BunchMonitor(
        0,
        save_every=1,
        buffer_size=1000,
        total_size=n_turns,
        file_name=monitor_filename,
        mpi_mode=False,
    )
    long_map = LongitudinalMap(ring)
    main_rf = RFCavity(ring, m=1, Vc=Vc, theta=np.arccos(ring.U0 / Vc))
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)

    esrf_wakedata = np.loadtxt(folder + 'full_wake.txt', delimiter=',')
    Wz = WakeFunction(esrf_wakedata[:,0]/c, esrf_wakedata[:,1], component_type='long')
    Wdy = WakeFunction(esrf_wakedata[:,0]/c,
                       -esrf_wakedata[:,3]/ring.optics.beta(0)[1], component_type='ydip')
    Wqy = WakeFunction(esrf_wakedata[:,0]/c,
                       -esrf_wakedata[:,5]/ring.optics.beta(0)[1], component_type='yquad')
    Wqx = WakeFunction(esrf_wakedata[:,0]/c,
                       -esrf_wakedata[:,4]/ring.optics.beta(0)[0], component_type='xquad')
    wakefield_tr = WakePotential(ring, WakeField([Wz, Wdy, Wqy, Wqx]))
    wakefield_long = WakePotential(ring, WakeField([Wz, Wqy, Wqx]))

    wakepotential_monitor = WakePotentialMonitor(
        bunch_number=0,
        wake_types="Wydip",
        n_bin=n_bin,
        save_every=1,
        buffer_size=600,
        total_size=2400,
        file_name=None,
        mpi_mode=False,
    )
    tracking_elements = [trans_map, long_map, bunch_monitor]
    tracking_elements.append(sr)
    if sc:
        besc = TransverseSpaceCharge(ring=ring,
                                     interaction_length=ring.L,
                                     n_bins=100)
        print('space charge included')
        tracking_elements.append(besc)
    else:
        print('space-charge weakened')
    print("Harmonic cavity is off.")
    tracking_elements.append(main_rf)

    monitor_count = 0
    track_wake_monitor = False
    stdx, stdy = mybunch.std[0], mybunch.std[2]
    try:
        for i in tqdm(range(n_turns)):
            for el in tracking_elements:
                el.track(mybunch)
            if i > 25_000:
                wakefield_tr.track(mybunch)
                if (np.mean(mybunch.mean[:][0]) > 0.1 * stdx
                    or np.mean(mybunch.mean[:][2]) > 0.1 * stdy and monitor_count < 2500):
                    track_wake_monitor = True
                if ((i > (n_turns - 2500)
                    or track_wake_monitor)
                        and monitor_count < 2500):
                    wakepotential_monitor.track(mybunch, wakefield_tr)
                    monitor_count += 1
            else:
                wakefield_long.track(mybunch)
    finally:
        bunch_monitor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Track transverse instabilities for ESRF-EBS storage ring.

    Supports both CLI arguments and TOML configuration files. CLI arguments
    override values from the config file. If no config file is provided,
    all simulation parameters must be specified via CLI or will use defaults.

    Example usage:
      # Using config file only:
      python track_esrf.py --config_file config.toml

    """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-c', '--config_file', metavar='CONFIG_FILE', type=str,
                        default=None,
                        help='Path to TOML configuration file. CLI args override config values.')
    args = parser.parse_args()

    config_path = args.config_file
    if config_path:
        full_config = load_toml_config(config_path)
        if 'script' in full_config:
            config = full_config['script']
        else:
            config = full_config
    else:
        config = {}

    run_mbtrack2(config)
