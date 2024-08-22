import os

pypath = os.getenv('PYTHONPATH')
pypath = pypath + ':/home/dockeruser/machine_data'
os.environ['PYTHONPATH'] = pypath
import numpy as np
from machine_data.soleil import v2366_v3
from mbtrack2.impedance.wakefield import WakeField
from mbtrack2.tracking import (Beam, Bunch, LongitudinalMap, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from tqdm import tqdm
from utils import get_parser_for_single_bunch
from setup_tracking import get_active_cavity_params, setup_fbt, setup_wakes, setup_rf

def run_mbtrack2(folder,
                 n_turns=100_000,
                 n_macroparticles=int(1e5),
                 n_bin=100,
                 bunch_current=1e-3,
                 Qp_x=1.6,
                 Qp_y=1.6,
                 id_state="open",
                 include_Zlong="False",
                 harmonic_cavity="False",
                 max_kick=1.6e-6,
                 sc='False'):
    Vc = 1.7e6
    ring = v2366_v3(IDs=id_state, HC_power=50e3, V_RF=Vc)
    ring.tune = np.array([54.23, 18.21])
    ring.chro = [Qp_x, Qp_y]
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
        f"max_kick={max_kick:.1e},"+\
        f"sc={sc:})"
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
    
    wakefield_tr, wakefield_long, _ = setup_wakes(ring, id_state, include_Zlong, n_bin)
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
    fbtx, fbty = setup_fbt(ring, max_kick)
    tracking_elements = [trans_map, long_map, bunch_monitor]
    if include_Zlong == 'True':
        tracking_elements.append(sr)
    besc = TransverseSpaceCharge(ring=ring,
                                interaction_length=ring.L,
                                n_bins=100)

    if sc == 'True':
        print('space charge included')
        tracking_elements.append(besc)
    if harmonic_cavity == "True":
        print("Harmonic cavity is on.")
        tracking_elements.append(main_rf)
        tracking_elements.append(harmonic_rf)
    else:
        print("Harmonic cavity is off.")
        tracking_elements.append(main_rf)
    if max_kick != 0:
        tracking_elements.append(fbtx)
        tracking_elements.append(fbty)

    monitor_count = 0
    track_wake_monitor = False
    stdx, stdy = bunch.std[0], bunch.std[2]
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
            elif include_Zlong == 'True':
                wakefield_long.track(mybunch)
    finally:
        bunch_monitor.close()


if __name__ == "__main__":
    parser = get_parser_for_single_bunch()
    args = parser.parse_args()
    folder = "/home/dockeruser/transverse_instabilities/data/raw/sbi/"
    run_mbtrack2(folder=folder,
                 n_turns=args.n_turns,
                 n_macroparticles=args.n_macroparticles,
                 n_bin=args.n_bin,
                 bunch_current=args.bunch_current,
                 Qp_x=args.Qp_x,
                 Qp_y=args.Qp_y,
                 id_state=args.id_state,
                 include_Zlong=args.include_Zlong,
                 harmonic_cavity=args.harmonic_cavity,
                 max_kick=args.max_kick,
                 sc=args.sc)
