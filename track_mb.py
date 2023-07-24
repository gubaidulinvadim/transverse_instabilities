import numpy as np
from utils import  get_parser_for_single_bunch
from scipy.constants import c
from tqdm import tqdm
import h5py as hp
import matplotlib.pyplot as plt
from mbtrack2 import Synchrotron, Electron
from mbtrack2.utilities import Optics
from mbtrack2.tracking import LongitudinalMap, SynchrotronRadiation, TransverseMap
from mbtrack2.tracking import Beam, Bunch, WakePotential
from mbtrack2.tracking import RFCavity, SynchrotronRadiation
from mbtrack2.tracking.monitors import WakePotentialMonitor, BeamMonitor
from machine_data.TDR2 import *
from machine_data.soleil import v2366
from SOLEILII_parameters.SOLEILII_TDR_parameters import *
FOLDER = '/home/dockeruser/mbtrack2_transverse_instabilities/'

def run_mbtrack2(n_turns=50000, n_macroparticles=int(1e5), n_bin=100, bunch_current=1e-3, Qp_x=1.6, Qp_y=1.6, ID_state='open', include_Zlong=False, n_turns_wake=1):
    ring2 = v2366(IDs=ID_state, load_lattice=False)
    particle = Electron()
    chro = [Qp_x, Qp_y]
    ring = Synchrotron(h=ring2.h, optics=ring2.optics, particle=particle, L=ring2.L, E0=ring2.E0, ac=ring2.ac, 
                    U0=ring2.U0, tau=ring2.tau, emit=ring2.emit, tune=ring2.tune, 
                    sigma_delta=ring2.sigma_delta, sigma_0=ring2.sigma_0, chro=chro)
    np.random.seed(42)
    beam = Beam(ring)
    filling_pattern = np.ones(ring.h)*bunch_current
    beam.init_beam(filling_pattern, mp_per_bunch=n_macroparticles)
    monitor_filename = FOLDER+'monitors(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f})'.format(
        n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y 
    ) 
    beam_monitor = BeamMonitor(ring.h, save_every=1, buffer_size=500, file_name=monitor_filename, total_size=n_turns, mpi_mode=True)
    long_map = LongitudinalMap(ring)
    rf = RFCavity(ring, m=1, Vc=V_RF, theta=np.arccos(ring.U0/V_RF))
    sr = SynchrotronRadiation(ring, switch=[1, 0, 0])
    trans_map = TransverseMap(ring)
    wakemodel = load_TDR2_wf(version=('TDR2.1_ID'+ID_state))
    wakemodel.drop(['Zlong', 'Zxdip', 'Zydip', 'Wxdip'])
    if not include_Zlong: 
        wakemodel.drop(['Wlong'])
    wakefield = WakePotential(ring, wakemodel, n_bin=n_bin)
    long_wakefield = LongRangeResistiveWall(
                                            ring=ring,
                                            beam=beam,
                                            length=350.749,
                                            rho=2.135e-8,
                                            radius=5e-3,
                                            types=['Wydip'],
                                            nt=n_turns_wake,
                                            x3=6.38e-3,
                                            y3=6.73e-3,
)
    # wakepotential_monitor = WakePotentialMonitor(bunch_number=0, wake_types='Wydip', n_bin=n_bin, save_every=1, 
                    # buffer_size=100, total_size=2400, file_name=None, mpi_mode=True)
    for i in tqdm(range(n_turns)):
        trans_map.track(beam)
        long_map.track(beam)
        rf.track(beam)
        wakefield.track(beam)
        sr.track(beam)
        long_wakefield.track(beam)
        beam_monitor.track(beam)
if __name__=='__main__':
    parser = get_parser_for_single_bunch()
    parser.add_argument('--n_turns_wake', action='store', metavar='N_TURNS_WAKE', type=int, default=1,
                        help='Number of turns for long range wakefield calculation. Defaults to 1')
    args = parser.parse_args()
    run_mbtrack2(n_turns=args.n_turns,
                n_macroparticles=args.n_macroparticles,
                n_bin=args.n_bin,
                bunch_current=args.bunch_current,
                Qp_x=args.Qp_x,
                Qp_y=args.Qp_y,
                ID_state=args.ID_state,
                include_Zlong=args.include_Zlong,
                n_turns_wake=args.n_turns_wake)