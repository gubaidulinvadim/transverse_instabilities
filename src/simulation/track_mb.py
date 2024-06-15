import os

pypath = os.getenv('PYTHONPATH')
pypath = pypath + ':/home/dockeruser/machine_data'
os.environ['PYTHONPATH'] = pypath
import numpy as np
from machine_data.soleil import v2366_v3
from mbtrack2 import DirectFeedback
from mbtrack2.tracking import (Beam, Bunch, CavityResonator, LongitudinalMap,
                               LongRangeResistiveWall, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.monitors import BeamMonitor
from tqdm import tqdm
from utils import get_parser_for_single_bunch
from setup_tracking import setup_fbt, setup_wakes, setup_dual_rf


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
    ring = v2366_v3(IDs=id_state, V_RF=Vc)
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
    sr = SynchrotronRadiation(ring, switch=[1, 1, 1])
    trans_map = TransverseMap(ring)
    wakefield_tr, wakefield_long, wakemodel = setup_wakes(ring, id_state, include_Zlong, n_bin)

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

    rf, hrf = setup_dual_rf(ring, beam, harmonic_cavity, bunch_current,  wakemodel)
    fbtx, fbty = setup_fbt(ring, max_kick)
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
