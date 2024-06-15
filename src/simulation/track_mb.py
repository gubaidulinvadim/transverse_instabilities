import os

pypath = os.getenv('PYTHONPATH')
pypath = pypath + ':/home/dockeruser/machine_data'
os.environ['PYTHONPATH'] = pypath
import h5py as hp
import matplotlib.pyplot as plt
# os.system('echo ${PYTHONPATH}')
# os.system('pip list')
import numpy as np
from machine_data.soleil import v2366, v2366_v2
from machine_data.TDR2 import *
from mbtrack2 import DirectFeedback
from mbtrack2.impedance.wakefield import WakeField
from mbtrack2.tracking import (Beam, Bunch, CavityResonator, LongitudinalMap,
                               LongRangeResistiveWall, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.feedback import ExponentialDamper, FIRDamper
from mbtrack2.tracking.monitors import BeamMonitor
from mbtrack2.utilities import Optics
from scipy.constants import c
from tqdm import tqdm
from utils import get_parser_for_single_bunch

def run_mbtrack2(folder,
                 n_turns=50_000,
                 n_macroparticles=int(1e5),
                 n_bin=100,
                 bunch_current=1.2e-3,
                 Qp_x=1.6,
                 Qp_y=1.6,
                 id_state="open",
                 include_Zlong="False",
                 harmonic_cavity="False",
                 n_turns_wake=1,
                 max_kick=1.6e-6):
    Vc = 1.7e6
    ring = v2366_v2(IDs=id_state, V_RF=Vc)
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
        "monitors(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f},ID_state={:},include_Zlong={:},harmonic_cavity={:},n_turns_wake={:},max_kick={:.1e})"
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y,
                id_state, include_Zlong, harmonic_cavity, n_turns_wake,
                max_kick))
    beam_monitor = BeamMonitor(
        ring.h,
        save_every=100,
        buffer_size=500,
        file_name=monitor_filename,
        total_size=n_turns,
        mpi_mode=is_mpi,
    )
    long_map = LongitudinalMap(ring)
    rf = RFCavity(ring, m=1, Vc=Vc, theta=np.arccos(ring.U0 / Vc))
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)
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

    x3 = 6.38e-3
    if id_state == "open":
        y3 = 6.73e-3
    if id_state == "close":
        y3 = 5.50e-3
    long_wakefield = LongRangeResistiveWall(
        ring=ring,
        beam=beam,
        length=350.749,
        rho=2.135e-8,
        radius=8e-3,
        types=["Wydip"],
        nt=n_turns_wake,
        x3=x3,
        y3=y3,
    )

    if harmonic_cavity == "True":
        Vc = 1.7e6
        Itot = ring.h * bunch_current  # Use for fixed detuning or CT
        HC_det = 110e3  # Use for fixed detuning or CT
        HC_det_end = 3e3
        MC_det = -35e3
        xi_start = 1.15
        xi_end = 1.2
        estimated_bunch_length = 40e-12

        # FB Settings
        fb_gain = [0.01, 1000]  # fb Gain for IQ components of Vc
        fb_sample_num = (
            208  # 2*2*2*2*3*3*3, mean Vc value of this number is used for Vg control
        )
        fb_every = 208  # 192ns (assumption),corresponding to process speed of the Feedback system
        fb_delay = 704  # int(2e-6/ring.T1)
        directFB_gain = 0.1
        directFB_phaseShift = 0 / 180 * np.pi
        tuner_gain = 0.01
        PFB_gainA = 0.01
        PFB_gainP = 0.01
        PFB_delay = 1
        m = 1
        Rs = 5e6
        Q = 35.7e3
        QL = 6e3
        detune = MC_det
        Ncav = 4
        rf = CavityResonator(ring, m, Rs, Q, QL, detune, Ncav=Ncav)

        m = 4
        Rs = 2.358e6
        Q = 36e3
        QL = 36e3
        Ncav = 1
        hrf = CavityResonator(ring, m, Rs, Q, QL, detune, Ncav=Ncav)
        hrf.Vg = 0
        hrf.theta_g = 0
        hrf.detune = HC_det

        HC_det = Itot * hrf.Rs / hrf.Q * ring.f1 / Vc * hrf.m**2 / xi_start
        hrf.detune = HC_det
        HC_det_end = Itot * hrf.Rs / hrf.Q * ring.f1 / Vc * hrf.m**2 / xi_end

        delta = 0
        delta += hrf.Vb(Itot) * np.cos(hrf.psi)
        delta += beam[0].charge * wakemodel.Wlong.loss_factor(
            estimated_bunch_length)

        rf.Vc = Vc
        rf.theta = np.arccos((ring.U0 + delta) / Vc)
        # rf.set_optimal_detune(Itot)
        rf.set_generator(Itot)

        dfb = DirectFeedback(
            ring=ring,
            cav_res=rf,
            gain=fb_gain,
            sample_num=fb_sample_num,
            every=fb_every,
            delay=fb_delay,
            DFB_gain=directFB_gain,
            DFB_phase_shift=directFB_phaseShift,
        )
        rf.feedback.append(dfb)
        rf.init_phasor(beam)
        hrf.init_phasor(beam)

    # fbty = FIRDamper(ring,
    #                 plane='y',
    #                 tune=ring.tune[1],
    #                 turn_delay=1,
    #                 tap_number=7,
    #                 gain=1,
    #                 phase=90,
    #                 bpm_error=None,
    #                 max_kick=max_kick)
    # fbtx = FIRDamper(ring,
    #                 plane='x',
    #                 tune=ring.tune[0],
    #                 turn_delay=1,
    #                 tap_number=7,
    #                 gain=1,
    #                 phase=90,
    #                 bpm_error=None,
    #                 max_kick=max_kick)

    feedback_tau = max_kick / 1.8e-6 * 50
    fbty = ExponentialDamper(ring,
                             plane='y',
                             damping_time=ring.T0 * feedback_tau,
                             phase_diff=np.pi / 2)
    fbtx = ExponentialDamper(ring,
                             plane='x',
                             damping_time=ring.T0 * feedback_tau,
                             phase_diff=np.pi / 2)

    tracking_elements = [trans_map, long_map, sr, beam_monitor, rf]

    if harmonic_cavity == 'True':
        tracking_elements.append(hrf)
    if max_kick != 0:
        tracking_elements.append(fbtx)
        tracking_elements.append(fbty)

    for i in range(n_turns):
        if i % 1000 == 0:
            if is_mpi:
                if beam.mpi.rank == 0:
                    print(f"mpi Turn {i:}")
            else:
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
        elif include_Zlong == 'True':
            wakefield_long.track(beam)


if __name__ == "__main__":
    parser = get_parser_for_single_bunch()
    parser.add_argument(
        "--n_turns_wake",
        action="store",
        metavar="N_TURNS_WAKE",
        type=int,
        default=1,
        help=
        "Number of turns for long range wakefield calculation. Defaults to 1",
    )
    args = parser.parse_args()
    folder = "/home/dockeruser/transverse_instabilities/data/raw/tcbi/"
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
                 n_turns_wake=args.n_turns_wake,
                 max_kick=args.max_kick)
