import os

pypath = os.getenv('PYTHONPATH')
pypath = pypath + ':/home/dockeruser/machine_data'
os.environ['PYTHONPATH'] = pypath
import h5py as hp
import matplotlib.pyplot as plt
import numpy as np
from machine_data.soleil import v2366_v3
from machine_data.TDR2 import *
from mbtrack2.impedance.wakefield import WakeField
from mbtrack2.tracking import (Beam, Bunch, LongitudinalMap, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.feedback import ExponentialDamper, FIRDamper
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from mbtrack2.utilities import Optics
from scipy.constants import c
from tqdm import tqdm
from utils import get_active_cavity_params, get_parser_for_single_bunch



def setup_rf(ring, harmonic_cavity, Vc):
    if harmonic_cavity == "False":
        main_rf = RFCavity(ring, m=1, Vc=Vc, theta=np.arccos(ring.U0 / Vc))
        harmonic_rf = None
    if harmonic_cavity == "True":
        V_main, theta_main, V_harmonic, theta_harmonic = get_active_cavity_params(
            ring)
        main_rf = RFCavity(ring, m=1, Vc=V_main, theta=theta_main)
        harmonic_rf = RFCavity(ring,
                               m=4,
                               Vc=V_harmonic,
                               theta=theta_harmonic)
    return main_rf, harmonic_rf


def setup_wakes(ring, id_state, include_Zlong, n_bin):
    wakemodel = load_TDR2_wf(version=("TDR2.1_ID" + id_state))
    
    if include_Zlong == 'True':
        wakefield_tr = WakePotential(ring,
                                     wakefield=WakeField(
                                         [wakemodel.Wydip, wakemodel.Wlong]),
                                     n_bin=n_bin)
    else:
        wakefield_tr = WakePotential(ring,
                                     wakefield=WakeField([wakemodel.Wydip]),
                                     n_bin=n_bin)
    
    wakefield_long = WakePotential(ring,
                                   wakefield=WakeField([wakemodel.Wlong]),
                                   n_bin=n_bin)
    return wakefield_tr, wakefield_long


def setup_fbt(ring, max_kick, kind='exp'):
    if kind == 'exp':
        feedback_tau = max_kick / 1.8e-6 * 50
        fbty = ExponentialDamper(ring,
                                plane='y',
                                damping_time=ring.T0 * feedback_tau,
                                phase_diff=np.pi / 2)
        fbtx = ExponentialDamper(ring,
                                plane='x',
                                damping_time=ring.T0 * feedback_tau,
                                phase_diff=np.pi / 2)
    else:
        fbty = FIRDamper(ring,
                        plane='y',
                        tune=ring.tune[1],
                        turn_delay=1,
                        tap_number=7,
                        gain=1,
                        phase=90,
                        bpm_error=None,
                        max_kick=max_kick)
        fbtx = FIRDamper(ring,
                        plane='x',
                        tune=ring.tune[0],
                        turn_delay=1,
                        tap_number=7,
                        gain=1,
                        phase=90,
                        bpm_error=None,
                        max_kick=max_kick)
    return fbtx, fbty


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
        f"bunch_current={bunch_current:.1e},"+\
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
    
    wakefield_tr, wakefield_long = setup_wakes(version, id_state, include_Zlong, ring, n_bin)
    wakepotential_monitor = WakePotentialMonitor(
        bunch_number=0,
        wake_types="Wydip",
        n_bin=n_bin,
        save_every=1,
        buffer_size=500,
        total_size=2500,
        file_name=None,
        mpi_mode=False,
    )
    fbtx, fbty = setup_fbt(ring, max_kick)
    tracking_elements = [trans_map, long_map, bunch_monitor]
    if include_Zlong == 'True':
        tracking_elements.append(sr)
    besc = TransverseSpaceCharge(interaction_length=ring.L,
                                 energy=ring.E0,
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
    for i in tqdm(range(n_turns)):
        for el in tracking_elements:
            el.track(mybunch)
        if i > 25_000:
            wakefield_tr.track(mybunch)
            if ((i > (n_turns - 2500)
                 or np.mean(mybunch.particles["x"]) > 0.1 * stdx
                 or np.mean(mybunch.particles["y"]) > 0.1 * stdy)
                    and monitor_count < 2500):
                wakepotential_monitor.track(mybunch, wakefield_tr)
                monitor_count += 1
        elif include_Zlong == 'True':
            wakefield_long.track(mybunch)


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
