import numpy as np
from mbtrack2.impedance.wakefield import WakeField
from mbtrack2.tracking import (Bunch, LongitudinalMap, RFCavity,
                               SynchrotronRadiation, TransverseMap,
                               WakePotential)
from mbtrack2.impedance.wakefield import WakeField, WakeFunction
from mbtrack2.tracking.monitors import BunchMonitor, WakePotentialMonitor
from mbtrack2.tracking.spacecharge import TransverseSpaceCharge
from tqdm import tqdm
from utils import get_parser_for_single_bunch
from esrf_ebs import esrf_ebs
from scipy.constants import c

def run_mbtrack2(folder,
                 n_turns=100_000,
                 n_macroparticles=int(1e5),
                 n_bin=100,
                 bunch_current=1e-3,
                 Qp_x=1.6,
                 Qp_y=1.6,
                 sc='False',
                 ):
    Vc = 6e6
    ring = esrf_ebs()
    ring.chro = np.array([Qp_x, Qp_y])
    ring.emit[1] = 10e-12 
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
    
    # wakefield_tr, wakefield_long, _ = setup_wakes(ring, id_state, include_Zlong, n_bin)
    esrf_wakedata = np.loadtxt('../../data/input/full_wake.txt', delimiter=',')
    Wz = WakeFunction(esrf_wakedata[:,0]/c, esrf_wakedata[:,1], component_type='long', )
    # Wdx = WakeFunction(esrf_wakedata[:,0]/c, esrf_wakedata[:,2], component_type='xdip')
    Wdy = WakeFunction(esrf_wakedata[:,0]/c,
                       esrf_wakedata[:,3]/ring.optics.local_beta[1]**2, component_type='ydip')
    # Wqx = WakeFunction(esrf_wakedata[:,0]/c, esrf_wakedata[:,4], component_type='xquad')
    Wqy = WakeFunction(esrf_wakedata[:,0]/c,
                       esrf_wakedata[:,5]/ring.optics.local_beta[1]**2, component_type='yquad')
    # wf_esrf = WakeField([Wz, Wdx, Wdy, Wqx, Wqy], name="ESRF wakefield", )
    wakefield_tr = WakePotential(ring, WakeField([Wz, Wdy, Wqy]))
    wakefield_long = WakePotential(ring, WakeField([Wz]))
                            

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
    if sc == 'True':
        besc = TransverseSpaceCharge(ring=ring,
                                    interaction_length=ring.L,
                                    n_bins=100)
        print('space charge included')
        tracking_elements.append(besc)
    else:
        ring.emit[1] = 40e-12
        besc = TransverseSpaceCharge(ring=ring,
                                    interaction_length=ring.L,
                                    n_bins=100)
        print('space-charge weakened')
        
        tracking_elements.append(besc)
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
                    track_wake_monitor=True
                if ((i > (n_turns - 2500)
                    or track_wake_monitor)
                        and monitor_count < 2500):
                    wakepotential_monitor.track(mybunch, wakefield_tr)
                    monitor_count += 1
            else:
                wakefield_long.track(mybunch)
    finally:
        print('F')
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
                 sc=args.sc, 
                 )
