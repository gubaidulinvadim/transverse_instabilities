import numpy as np
import os, sys
os.environ["PYTHONPATH"] += os.pathsep + "/home/dockeruser/facilities_mbtrack2/"
sys.path.append('/home/dockeruser/facilities_mbtrack2')
from facilities_mbtrack2.SOLEIL_II import v3633
from mbtrack2.tracking import (Bunch, LongitudinalMap, 
                               SynchrotronRadiation, TransverseMap,
                               )
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from mbtrack2.tracking.ibs import IntrabeamScattering
from tqdm import tqdm
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_toml_config
from setup_tracking import setup_fbt, setup_wakes, setup_rf

# def run_mbtrack2(folder: str,
#                  n_turns: int = 100_000,
#                  n_macroparticles: int = 100_000,
#                  n_bin: int = 100,
#                  bunch_current: float = 1e-3,
#                  Qp_x: float = 1.6,
#                  Qp_y: float = 1.6,
#                  id_state: str = "open",
#                  include_Zlong: str = "False",
#                  harmonic_cavity: str = "False",
#                  max_kick: float = 1.6e-6,
#                  sc: str = 'False',
#                  ibs: str = 'False',
#                  quad: str = 'False',
#                  wake_y: str = 'True') -> None:
def run_mbtrack2(config: dict) -> None:
    folder = config['folder']
    n_turns = config.get('n_turns', 100_000)
    n_macroparticles = config.get('n_macroparticles', 100_000)
    n_bin = config.get('n_bin', 100)
    bunch_current = config.get('bunch_current', 1e-3)
    Qp_x = config.get('Qp_x', 1.6)
    Qp_y = config.get('Qp_y', 1.6)
    id_state = config.get('id_state', "open")
    include_Zlong = config.get('include_Zlong', False)
    harmonic_cavity = config.get('harmonic_cavity', False)
    feedback_tau = config.get('feedback_tau', 0.01)
    sc = config.get('sc', False)
    ibs = config.get('ibs', False)
    quad = config.get('quad', False)
    wake_y = config.get('wake_y', True)

    Vc = 1.7e6
    ring = v3633(IDs=id_state, HC_power=50e3, V_RF=Vc, load_lattice=True)
    ring.tune = np.array([54.23, 18.21])
    ring.chro = np.array([Qp_x, Qp_y])  
    ring.emit[1] = 0.3 * ring.emit[0]
    mybunch = Bunch(ring,
                    mp_number=n_macroparticles,
                    current=bunch_current,
                    track_alive=False)
    np.random.seed(42)
    mybunch.init_gaussian()
    stdx, stdy = np.std(mybunch['x']), np.std(mybunch['y'])
    monitor_filename = folder + f"monitors(n_mp={n_macroparticles:.1e}," + \
        f"n_turns={n_turns:.1e}," +\
        f"n_bin={n_bin:},"+\
        f"bunch_current={bunch_current:.2e},"+\
        f"Qp_x={Qp_x:.2f},"+\
        f"Qp_y={Qp_y:.2f},"+\
        f"id_state={id_state:},"+\
        f"Zlong={include_Zlong:},"+\
        f"cavity={harmonic_cavity:},"+\
        f"feedback_tau={feedback_tau:.1e},"+\
        f"sc={sc:},"+\
        f"ibs={ibs:}"+\
        f"quad={quad:}"+\
        f"wake_y={wake_y:}"\
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
    main_rf, harmonic_rf = setup_rf(ring, harmonic_cavity, Vc)
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)
    
    wakefield_tr, wakefield_long, _ = setup_wakes(ring, id_state,
                                                  include_Zlong, n_bin,
                                                  quad, wake_y)
    wakepotential_monitor = WakePotentialMonitor(
        bunch_number=0,
        wake_types='Wydip',
        n_bin=n_bin,
        save_every=1,
        buffer_size=600,
        total_size=2400,
        file_name=None,
        mpi_mode=False,
    )
    tracking_elements = [trans_map, long_map, bunch_monitor]
    if include_Zlong == 'True':
        tracking_elements.append(sr)
    besc = TransverseSpaceCharge(ring=ring,
                                interaction_length=ring.L,
                                n_bins=100)
    ibs_cimp = IntrabeamScattering(ring, model="CIMP", n_points=100, n_bin=100)
    if ibs:
        print('IBS included')
        tracking_elements.append(ibs_cimp)
    if sc:
        print('space charge included')
        tracking_elements.append(besc)
    if harmonic_cavity:
        print("Harmonic cavity is on.")
        tracking_elements.append(main_rf)
        tracking_elements.append(harmonic_rf)
    else:
        print("Harmonic cavity is off.")
        tracking_elements.append(main_rf)
    if feedback_tau != 0:
        fbtx, fbty = setup_fbt(ring, max_kick)
        tracking_elements.append(fbtx)
        tracking_elements.append(fbty)

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
                    track_wake_monitor=True
                if ((i > (n_turns - 2500)
                    or track_wake_monitor)
                        and monitor_count < 2500):
                    wakepotential_monitor.track(mybunch, wakefield_tr)
                    monitor_count += 1
            elif include_Zlong:
                wakefield_long.track(mybunch)
    finally:
        bunch_monitor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description="""Track beam-ion instability in a light source storage ring.

    Supports both CLI arguments and TOML configuration files. CLI arguments
    override values from the config file. If no config file is provided,
    all simulation parameters must be specified via CLI or will use defaults.

    Example usage:
      # Using config file only:
      python track_TI.py --config config.toml

    """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

    # Config file argument (optional, for backward compatibility)
    parser.add_argument('-c', '--config', metavar='CONFIG_FILE', type=str,
                        default=None,
                        help='Path to TOML configuration file. CLI args override config values.')
    args = parser.parse_args()


    
    config_path = args.config if args.config else args.config_file
    if config_path:
        full_config = load_toml_config(config_path)

    # Support both 'script' section (for backward compatibility) and flat structure
        if 'script' in full_config:
            config = full_config['script']
        else:
           config = full_config
    else:
        config = {}

    # folder = "/home/dockeruser/transverse_instabilities/data/raw/sbi/"
    run_mbtrack2(config)
