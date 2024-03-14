import numpy as np
from utils import get_parser_for_single_bunch
from scipy.constants import c
from tqdm import tqdm
import h5py as hp
import matplotlib.pyplot as plt
from mbtrack2 import Synchrotron, Electron
from mbtrack2.utilities import Optics
from mbtrack2.tracking import LongitudinalMap, SynchrotronRadiation, TransverseMap
from mbtrack2.tracking import Beam, Bunch, WakePotential
from mbtrack2.tracking import RFCavity, SynchrotronRadiation
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.feedback import FIRDamper, ExponentialDamper
from machine_data.TDR2 import *
from machine_data.soleil import v2366, v2366_v2
from SOLEILII_parameters.SOLEILII_TDR_parameters import *

FOLDER = "/home/dockeruser/mbtrack2_transverse_instabilities/"
# FOLDER = '/home/gubaidulin/scripts/tracking/mbtrack2_transverse_instabilities/'


def run_mbtrack2(
    n_turns=100_000,
    n_macroparticles=int(1e5),
    n_bin=100,
    bunch_current=1e-3,
    Qp_x=1.6,
    Qp_y=1.6,
    id_state="open",
    include_Zlong="False",
    harmonic_cavity="False",
    max_kick=1.6e-6
):
    ring2 = v2366_v2(IDs="open")
    particle = Electron()
    chro = [Qp_x, Qp_y]
    ring = Synchrotron(
        h=ring2.h,
        optics=ring2.optics,
        particle=particle,
        L=ring2.L,
        E0=ring2.E0,
        ac=ring2.ac,
        U0=ring2.U0,
        tau=ring2.tau,
        emit=ring2.emit,
        tune=ring2.tune,
        sigma_delta=ring2.sigma_delta,
        sigma_0=ring2.sigma_0,
        chro=chro,
    )
    mybunch = Bunch(
        ring, mp_number=n_macroparticles, current=bunch_current, track_alive=False
    )
    np.random.seed(42)
    mybunch.init_gaussian()
    monitor_filename = "monitors(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f},id_state={:},Zlong={:},cavity={:},max_kick={:.1e})".format(
        n_macroparticles,
        n_turns,
        n_bin,
        bunch_current,
        Qp_x,
        Qp_y,
        id_state,
        include_Zlong,
        harmonic_cavity,
        max_kick
    )
    bunch_monitor = BunchMonitor(
        0,
        save_every=1,
        buffer_size=10,
        total_size=n_turns,
        file_name=monitor_filename,
        mpi_mode=False,
    )
    long_map = LongitudinalMap(ring)
    if harmonic_cavity == "False":
        rf = RFCavity(ring, m=1, Vc=V_RF, theta=np.arccos(ring.U0 / V_RF))
    if harmonic_cavity == "True":
        theta_main = 1.2753602707269827
        theta_harmonic = -1.7210480862530364
        V_RF_main = 1.78786174535864e6
        V_RF_harmonic = 0.4292124905802067e6
        main_rf = RFCavity(ring, m=1, Vc=V_RF_main, theta=theta_main)
        harmonic_rf = RFCavity(ring, m=4, Vc=V_RF_harmonic, theta=theta_harmonic)
    sr = SynchrotronRadiation(ring, switch=[1, 0, 0])
    trans_map = TransverseMap(ring)
    wakemodel = load_TDR2_wf(version=("TDR2.1_ID" + id_state))
    # wakemodel.drop(["Zlong", "Zxdip", "Zydip", "Wxdip"])
    # if include_Zlong == "False":
    #     print("Longitudinal impedance is turned off.")
    #     wakemodel.drop(["Wlong"])
    wakefield_tr = WakePotential(ring, wakemodel.Wydip, n_bin=n_bin)
    wakefield_long = WakePotential(ring, wakemodel.Wlong, n_bin=n_bin)
    
    wakepotential_monitor = WakePotentialMonitor(
        bunch_number=0,
        wake_types="Wydip",
        n_bin=n_bin,
        save_every=1,
        buffer_size=100,
        total_size=2400,
        file_name=None,
        mpi_mode=False,
    )

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

    # fbty = ExponentialDamper(ring, plane='y', damping_time=ring.T0*feedback_tau, phase_diff=np.pi/2)
    # fbtx = ExponentialDamper(ring, plane='x', damping_time=ring.T0*feedback_tau, phase_diff=np.pi/2)

    tracking_elements = [trans_map, long_map, sr, bunch_monitor]
    if harmonic_cavity == "True":
        print("Harmonic cavity is on.")
        tracking_elements.append([main_rf, harmonic_rf])
    else:
        print("Harmonic cavity is off.")
        tracking_elements.append(rf)
    if max_kick != 0:
        tracking_elements.append([fbtx, fbty])
    if include_Zlong:
        print("Longitudinal impedance included.")
        tracking_elements.append(wakefield_long)
    for i in tqdm(range(n_turns)):
        for el in tracking_elements:
            el.track(mybunch)
        if i > 10_000:
            wakefield_tr.track(mybunch)
        if (
            i > (n_turns - 2500)
            or np.mean(mybunch.particles["x"]) > 0.01
            or np.mean(mybunch.particles["y"]) > 0.01
        ):
            wakepotential_monitor.track(mybunch, wakefield_tr)

if __name__ == "__main__":
    parser = get_parser_for_single_bunch()
    args = parser.parse_args()
    run_mbtrack2(
        n_turns=args.n_turns,
        n_macroparticles=args.n_macroparticles,
        n_bin=args.n_bin,
        bunch_current=args.bunch_current,
        Qp_x=args.Qp_x,
        Qp_y=args.Qp_y,
        id_state=args.id_state,
        include_Zlong=args.include_Zlong,
        harmonic_cavity=args.harmonic_cavity,
        max_kick=args.max_kick
    )
