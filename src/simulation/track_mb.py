import os, sys
import numpy as np
os.environ["PYTHONPATH"] += os.pathsep + "/home/dockeruser/facilities_mbtrack2/"
sys.path.append('/home/dockeruser/facilities_mbtrack2')
from mbtrack2.tracking import (Beam, LongitudinalMap,
                               LongRangeResistiveWall,
                               SynchrotronRadiation, TransverseMap,
                               TransverseResonator)
from mbtrack2.tracking.monitors import (BeamMonitor, WakePotentialMonitor,
                                    CavityMonitor)
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_toml_config
from fill_patterns import build_filling_pattern
from monitor_filenames import get_monitor_filename
from setup_tracking import (setup_bunch_by_bunch_feedback, setup_dual_rf,
                            setup_wakes)
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from mbtrack2.tracking.ibs import IntrabeamScattering
from facilities_mbtrack2 import v3633


def run_mbtrack2(config: dict) -> None:

    n_turns = config.get('n_turns', 75_000)
    n_macroparticles = config.get('n_macroparticles', int(1e5))
    n_bin = config.get('n_bin', 100)
    bunch_current = config.get('bunch_current', 1.2e-3)
    Qp_x = config.get('Qp_x', 1.8)
    Qp_y = config.get('Qp_y', 1.4)
    id_state = config.get('id_state', "open")
    include_Zlong = config.get('include_Zlong', False)
    harmonic_cavity = config.get('harmonic_cavity', False)
    n_turns_wake = config.get('n_turns_wake', 50)
    feedback_tau = config.get('feedback_tau', 100)
    feedback_phase = config.get('feedback_phase', -90)
    sc = config.get('sc', False)
    ibs = config.get('ibs', False)
    wake_types = config.get('wake_types', ['Wydip'])
    emittance_ratio = config.get('emittance_ratio', 0.3)

    Vc = 1.7e6
    ring = v3633(IDs=id_state, HC_power=0, V_RF=Vc, load_lattice=True)
    ring.tune = np.array([54.23, 18.21])
    ring.chro = [Qp_x, Qp_y]
    ring.emit[1] = emittance_ratio * ring.emit[0]
    np.random.seed(42)
    beam = Beam(ring)
    is_mpi = True
    filling_pattern = build_filling_pattern(ring.h, bunch_current, config)
    n_bunches = int(np.count_nonzero(filling_pattern))
    total_current = float(np.sum(filling_pattern))
    fill_pattern_name = config.get('fill_pattern', 'full')
    print(
        f"Fill pattern: {fill_pattern_name}, {n_bunches} bunches, "
        f"total current={total_current:.6g} A"
    )
    beam.init_beam(
        filling_pattern,
        mp_per_bunch=n_macroparticles,
        track_alive=False,
        mpi=is_mpi,
    )
    monitor_filename = get_monitor_filename(
        config,
        tracking_script="track_mb.py",
        harmonic_number=ring.h,
    )
    beam_monitor = BeamMonitor(
        ring.h,
        save_every=1,
        buffer_size=100,
        file_name=monitor_filename,
        total_size=n_turns,
        mpi_mode=is_mpi,
    )
    monitored_wake_types = ['Wlong']
    monitored_wake_types += wake_types
    # wakepotential_monitor = WakePotentialMonitor(
    #     bunch_number=0,
    #     wake_types=monitored_wake_types,
    #     n_bin=n_bin,
    #     save_every=1,
    #     buffer_size=600,
    #     total_size=2400,
    #     file_name=None,
    #     mpi_mode=is_mpi,
    # )
    # maincavmon = CavityMonitor("rf", ring, file_name=None, save_every=100,
    #              buffer_size=100, total_size=n_turns/100, mpi_mode=is_mpi)
    #
    # harmcavmon = CavityMonitor("hrf", ring, file_name=None, save_every=100,
    #              buffer_size=100, total_size=n_turns/100, mpi_mode=is_mpi)

    long_map = LongitudinalMap(ring)
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)
    wakefield_tr, wakefield_long, wakemodel, _ = setup_wakes(ring, id_state,
                                                             include_Zlong,
                                                             n_bin,
                                                             wake_types,
                                                             csr_flag=False)

    if id_state == "open":
        x3 = 6.62e-3
        y3 = 6.70e-3
    elif id_state == 'close':
        x3 = 5.78e-3
        y3 = 5.61e-3
    else:
        x3 = None
        y3 = None
    if id_state == "open":
        x3_quad = -15.01e-3
        y3_quad = 15.63e-3
    elif id_state == 'close':
        x3_quad = -7.90e-3
        y3_quad = 8.87e-3
    else:
        x3_quad = None
        y3_quad = None
    wake_types = [item for item in wake_types if (item.endswith('dip') or
                      item.endswith('quad'))]
    long_wakefield = LongRangeResistiveWall(
        ring=ring,
        beam=beam,
        length=ring.L,
        rho=2.135e-8,
        radius=8e-3,
        types=wake_types,
        nt=n_turns_wake,
        x3 = x3,
        y3 = y3,
        x3_quad = x3_quad,
        y3_quad = y3_quad
    )
    vertical_tune_fraction = ring.tune[1] % 1
    resonator_harmonic = round(1.4e9 / ring.f0 + vertical_tune_fraction)
    transverse_resonator = TransverseResonator(
        ring=ring,
        Rs=48.5e3 * 12,
        Q=942,
        fr=ring.f0 * (resonator_harmonic - vertical_tune_fraction),
        n_bin=n_bin,
        plane='y',
    )

    rf, hrf = setup_dual_rf(ring, beam, harmonic_cavity, total_current,
                            wakemodel)
    tracking_elements = [rf, trans_map, long_map, sr, beam_monitor]
    
    if harmonic_cavity:
        tracking_elements.insert(0, hrf)
    besc = TransverseSpaceCharge(ring=ring,
                                interaction_length=ring.L,
                                n_bins=n_bin)
    ibs_cimp = IntrabeamScattering(ring, model="CIMP", n_points=100, n_bin=100)
    if ibs:
        print('IBS included')
        tracking_elements.append(ibs_cimp)
    if sc:
        if is_mpi and beam.mpi.rank == 0:
            print('space charge included')
        tracking_elements.append(besc)
    if feedback_tau != 0:
        fbtx, fbty = setup_bunch_by_bunch_feedback(
            ring,
            feedback_tau,
            feedback_phase,
        )
        tracking_elements.append(fbtx)
        tracking_elements.append(fbty)
    if include_Zlong:
        tracking_elements.append(wakefield_long)

    stdx, stdy = np.mean(beam.bunch_std[:][0]), np.mean(beam.bunch_std[:][2])
    track_wake_monitor = False
    monitor_count = 0
    try:
        for i in range(n_turns):
            if i % 100 == 0:
                print(f"Turn {i:}")
            if is_mpi:
                beam.mpi.share_distributions(beam, n_bin=n_bin)
                beam.mpi.share_means(beam)
                beam.mpi.share_stds(beam)
            for el in tracking_elements:
                el.track(beam)
                # maincavmon.track(beam, rf)
                # if harmonic_cavity:
                    # harmcavmon.track(beam, hrf)

            if i > 20_000:
                wakefield_tr.track(beam)
                long_wakefield.track(beam)
                if is_mpi:
                    beam.mpi.share_distributions(
                        beam,
                        dipole_plane=transverse_resonator.plane,
                        n_bin=n_bin,
                    )
                transverse_resonator.track(beam)
                
            # if (monitor_count < 2500 and (np.mean(beam.bunch_mean[:][0]) > 0.1 * stdx or np.mean(beam.bunch_mean[:][2]) > 0.1 * stdy)):
                # track_wake_monitor=True
            # if monitor_count < 2500 and (i > (n_turns - 2500) or track_wake_monitor):
                # wakepotential_monitor.track(beam, wakefield_tr)
                # monitor_count += 1
        
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
    parser.add_argument('-c', '--config_file', metavar='CONFIG_FILE', type=str,
                        default=None,
                        help='Path to TOML configuration file. CLI args override config values.')
    args = parser.parse_args()


    
    config_path = args.config_file
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
