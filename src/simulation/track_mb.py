import os, sys
import numpy as np
os.environ["PYTHONPATH"] += os.pathsep + "/home/dockeruser/facilities_mbtrack2/"
sys.path.append('/home/dockeruser/facilities_mbtrack2')
from mbtrack2.tracking import (Beam, LongitudinalMap,
                               LongRangeResistiveWall,
                               SynchrotronRadiation, TransverseMap)
from mbtrack2.tracking.monitors import BeamMonitor, WakePotentialMonitor
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_toml_config, merge_config_and_args
from setup_tracking import setup_fbt, setup_wakes, setup_dual_rf
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from mbtrack2.tracking.ibs import IntrabeamScattering
from facilities_mbtrack2 import v3633


def run_mbtrack2(config: dict) -> None:

    folder = config['folder']
    n_turns = config.get('n_turns', 100_000)
    n_macroparticles = config.get('n_macroparticles', int(1e5))
    n_bin = config.get('n_bin', 100)
    bunch_current = config.get('bunch_current', 1.2e-3)
    Qp_x = config.get('Qp_x', 1.6)
    Qp_y = config.get('Qp_y', 1.6)
    id_state = config.get('id_state', "open")
    include_Zlong = config.get('include_Zlong', False)
    harmonic_cavity = config.get('harmonic_cavity', False)
    n_turns_wake = config.get('n_turns_wake', 1)
    feedback_tau = config.get('feedback-tau', 1.e-2)
    sc = config.get('sc', False)
    ibs = config.get('ibs', False)
    quad = config.get('quad', False)

    Vc = 1.7e6
    ring = v3633(IDs=id_state, V_RF=Vc, load_lattice=True)
    ring.tune = np.array([54.23, 18.21])
    ring.chro = [Qp_x, Qp_y]
    ring.emit[1] = 0.3 * ring.emit[0]
    np.random.seed(42)
    beam = Beam(ring)
    is_mpi = True
    filling_pattern = np.ones(ring.h) * bunch_current
    beam.init_beam(
        filling_pattern,
        mp_per_bunch=n_macroparticles,
        track_alive=False,
        mpi=is_mpi,
    )
    monitor_filename = (
        folder +
        f"monitors(n_mp={n_macroparticles:.1e}"+
        f",n_turns={n_turns:.1e}"+
        f",n_bin={n_bin}"+
        f",bunch_current={bunch_current:.1e}"+
        f",Qp_x={Qp_x:.2f}"+
        f",Qp_y={Qp_y:.2f}"+
        f",ID_state={id_state:}"+
        f",include_Zlong={include_Zlong:}"+
        f",harmonic_cavity={harmonic_cavity:}"+
        f",n_turns_wake={n_turns_wake:}"
        f",feedback_tau={feedback_tau:.1e}"+
        f",sc={sc:}"+\
        f",ibs={ibs:}"+
        f"quad={quad:}"+
        ")")
    beam_monitor = BeamMonitor(
        ring.h,
        save_every=10,
        buffer_size=1000,
        file_name=monitor_filename,
        total_size=n_turns//10,
        mpi_mode=is_mpi,
    )
    wakepotential_monitor = WakePotentialMonitor(
        bunch_number=0,
        wake_types="Wydip",
        n_bin=n_bin,
        save_every=1,
        buffer_size=600,
        total_size=2400,
        file_name=None,
        mpi_mode=is_mpi,
    )
    long_map = LongitudinalMap(ring)
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)
    wakefield_tr, wakefield_long, wakemodel = setup_wakes(ring, id_state, include_Zlong, n_bin)

    if id_state == "open":
        x3 = 6.51e-3
        y3 = 6.70e-3
    else:
        x3 = 5.78e-3
        y3 = 5.61e-3
    long_wakefield = LongRangeResistiveWall(
        ring=ring,
        beam=beam,
        length=ring.L,
        rho=2.135e-8,
        radius=8e-3,
        types=["Wxdip", "Wydip"],
        nt=n_turns_wake,
        x3=x3,
        y3=y3,
    )
    
    if id_state == "open":
        x3 = -15.01e-3
        y3 = 15.63e-3
    else:
        x3 = -7.90e-3
        y3 = 8.87e-3
    long_wakefield_quad = LongRangeResistiveWall(
        ring=ring,
        beam=beam,
        length=ring.L,
        rho=2.135e-8,
        radius=8e-3,
        types=["Wxdip", "Wydip"],
        nt=n_turns_wake,
        x3=x3,
        y3=y3,
        )


    rf, hrf = setup_dual_rf(ring, beam, harmonic_cavity, bunch_current,  wakemodel)
    fbtx, fbty = setup_fbt(ring, feedback_tau)
    tracking_elements = [trans_map, long_map, sr, beam_monitor, rf]
    besc = TransverseSpaceCharge(ring=ring,
                                interaction_length=ring.L,
                                n_bins=n_bin)
    ibs_cimp = IntrabeamScattering(ring, model="CIMP", n_points=100, n_bin=100)
    if ibs == 'True':
        print('IBS included')
        tracking_elements.append(ibs_cimp)
    if sc == 'True':
        if is_mpi and beam.mpi.rank == 0:
            print('space charge included')
        tracking_elements.append(besc)
    if harmonic_cavity == 'True':
        tracking_elements.append(hrf)
    if feedback_tau != 0:
        tracking_elements.append(fbtx)
        tracking_elements.append(fbty)

    stdx, stdy = np.mean(beam.bunch_std[:][0]), np.mean(beam.bunch_std[:][2])
    track_wake_monitor = False
    monitor_count = 0
    try:
        for i in range(n_turns):
            if i % 1000 == 0:
                if is_mpi and beam.mpi.rank == 0:
                    print(f"mpi Turn {i:}")
                elif not is_mpi:
                    print(f"Turn {i:}")
            if is_mpi:
                beam.mpi.share_distributions(beam, n_bin=n_bin)
                beam.mpi.share_means(beam)
                beam.mpi.share_stds(beam)
            for el in tracking_elements:
                el.track(beam)

            if i > 25_000:
                wakefield_tr.track(beam)
                long_wakefield.track(beam)
                if quad == 'True':
                    long_wakefield_quad.track(beam)
            elif include_Zlong == 'True':
                wakefield_long.track(beam)
                
            if (monitor_count < 2500 and (np.mean(beam.bunch_mean[:][0]) > 0.1 * stdx or np.mean(beam.bunch_mean[:][2]) > 0.1 * stdy)):
                track_wake_monitor=True
            if monitor_count < 2500 and (i > (n_turns - 2500) or track_wake_monitor):
                wakepotential_monitor.track(beam, wakefield_tr)
                monitor_count += 1
        
    finally:
        beam_monitor.close()


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

    run_mbtrack2(config)
