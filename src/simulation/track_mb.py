import os
import numpy as np
from mbtrack2 import DirectFeedback
from mbtrack2.tracking import (Beam, Bunch, CavityResonator, LongitudinalMap,
                               LongRangeResistiveWall, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.tracking.monitors import BeamMonitor, WakePotentialMonitor
from tqdm import tqdm
from utils import get_parser_for_multibunch
from setup_tracking import setup_fbt, setup_wakes, setup_dual_rf
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge

pypath = os.getenv('PYTHONPATH', '')
pypath = f"{pypath}{os.pathsep}/home/dockeruser/machine_data" if pypath else '/home/dockeruser/machine_data'
os.environ['PYTHONPATH'] = pypath
from machine_data.soleil import v2366_v3


def run_mbtrack2(folder,
                 n_turns=100_000,
                 n_macroparticles=int(1e5),
                 n_bin=100,
                 bunch_current=1.2e-3,
                 Qp_x=1.6,
                 Qp_y=1.6,
                 id_state="open",
                 include_Zlong="False",
                 harmonic_cavity="False",
                 n_turns_wake=1,
                 max_kick=1.6e-6,
                 sc="False"):
    Vc = 1.7e6
    ring = v2366_v3(IDs=id_state, V_RF=Vc)
    ring.chro = [Qp_x, Qp_y]
    ring.emit[1] = 0.3 * ring.emit[0]
    np.random.seed(42)
    beam = Beam(ring)
    is_mpi = True
    filling_pattern = np.zeros(ring.h) * bunch_current
    filling_pattern[0] = bunch_current
    filling_pattern[103] = bunch_current
    filling_pattern[207] = bunch_current
    filling_pattern[311] = bunch_current
    
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
        f",max_kick={max_kick:.1e}"+
        f",sc={sc:}"+
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
    besc = TransverseSpaceCharge(ring=ring,
                                interaction_length=ring.L,
                                n_bins=n_bin)

    if sc == 'True':
        print('space charge included')
        tracking_elements.append(besc)
    if harmonic_cavity == 'True':
        tracking_elements.append(hrf)
    if max_kick != 0:
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
            elif include_Zlong == 'True':
                wakefield_long.track(beam)
                
            if (monitor_count < 2500 and (np.mean(beam.bunch_mean[:][0]) > 0.1 * stdx or np.mean(beam.bunch_mean[:][2]) > 0.1 * stdy)):
                track_wake_monitor=True
            if monitor_count < 2500 and (i > (n_turns - 2500) or track_wake_monitor):
                wakepotential_monitor.track(mybunch, wakefield_tr)
                monitor_count += 1
        
    finally:
        beam_monitor.close()


if __name__ == "__main__":
    parser = get_parser_for_multibunch()
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
                 max_kick=args.max_kick,
                 sc=args.sc,)
