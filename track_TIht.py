import numpy as np
from scipy.constants import c, e, m_p, epsilon_0, m_e
from joblib import Parallel, delayed
import sys

import PyHEADTAIL
import PyHEADTAIL.particles.generators as generators
from PyHEADTAIL.trackers.longitudinal_tracking import RFSystems, RFBucket
from PyHEADTAIL.impedances.wakes import WakeField, WakeSource, ResistiveWall
from PyHEADTAIL.particles import slicing
from tqdm import tqdm
from PyHEADTAIL.monitors.monitors import SliceMonitor
from matplotlib import pyplot as plt
from aps_figures.aps_one_column import *
from PyHEADTAIL.trackers.detuners import Chromaticity
from SOLEILII_parameters.SOLEILII_TDR_parameters import *
from PyHEADTAIL.radiation.radiation import SynchrotronRadiationTransverse, SynchrotronRadiationLongitudinal
from PyHEADTAIL.trackers.transverse_tracking import TransverseMap

def run_ht():
    np.random.seed(42)                            
    n_turns = 2049
    chromaticity = 0
    n_turns = 50000
    n_turns_slicemonitor = 2048                   
    n_macroparticles = int(1e5)                  
    n_segments = 1             
    gamma = 1 + ENERGY * e / (m_e * c**2)
    beta = np.sqrt(1 - gamma**-2)
    PHI_RF = np.arcsin(U_LOSS/V_RF) if (GAMMA**-2-GAMMA_T**-2) < 0 else pi+np.arcsin(U_LOSS/V_RF)
    print('Synchronous phase is {:.2f}'.format(PHI_RF))

    p0 = np.sqrt(gamma**2 - 1) * m_e * c
    s = np.arange(0, n_segments + 1) * CIRCUMFERENCE / n_segments
    alpha_x = ALPHA_X_SMOOTH * np.ones(n_segments)
    beta_x = BETA_X_SMOOTH * np.ones(n_segments)
    D_x = np.zeros(n_segments)
    alpha_y = ALPHA_Y_SMOOTH * np.ones(n_segments)
    beta_y = BETA_Y_SMOOTH * np.ones(n_segments)
    D_y = np.zeros(n_segments)

    long_map = RFSystems(CIRCUMFERENCE, [H_RF, ], [V_RF, ], [PHI_RF, ],
                         [ALPHA_0], gamma, mass=m_e, charge=e)
    print(
        'The resulting number of longitudinal oscillations \n a single particle makes in a single turn: {0:.5f}'.format(
        long_map.Q_s))
    bunch = generators.ParticleGenerator(macroparticlenumber=n_macroparticles, intensity=INTENSITY_PER_BUNCH, charge=e,
                                            gamma=gamma, mass=m_e, circumference=CIRCUMFERENCE,
                                            distribution_x=generators.gaussian2D(EPSILON_X),
                                            alpha_x=alpha_x, beta_x=beta_x,
                                            distribution_y=generators.gaussian2D(EPSILON_Y),
                                            alpha_y=alpha_y, beta_y=beta_y,
                                            limit_n_rms_x=3.5, limit_n_rms_y=3.5,
                                            distribution_z=generators.gaussian2D_asymmetrical(SIGMA_Z, SIGMA_DP),
                                            ).generate()

    n_wake_slices = 500                                     
    z_cuts = (-4.2*bunch.sigma_z(), 4.2*bunch.sigma_z())    
    print('Wake slicer range: ({0:.3f}, {1:.3f})'.format(z_cuts[0], z_cuts[1]))
    wake_slicer = slicing.UniformBinSlicer(                            
        n_slices=n_wake_slices, z_cuts=z_cuts)
    dt_min = SIGMA_Z*8/c/n_wake_slices                                 
    res_wall = ResistiveWall(pipe_radius=6.77e-3,                      
                              resistive_wall_length=CIRCUMFERENCE,     
                              dt_min=dt_min,                           
                              Yokoya_X1=0,
                              Yokoya_X2 = 0,
                              Yokoya_Y2 = 0,
                              Yokoya_Y1=1,
                              conductivity=1/2.135e-8 )          
    wake_field = WakeField(wake_slicer, res_wall)
    print('Transverse radiation damping times in turns {:.0f}, {:.0f}'.format(TAU_X*OMEGA_REV/(2*np.pi), TAU_Y*OMEGA_REV/(2*np.pi)))
    print('Longitudinal radiation damping times in turns {:.0f}'.format(TAU_Z*OMEGA_REV/(2*np.pi)))
    synchr_rad = SynchrotronRadiationTransverse(eq_emit_x = bunch.epsn_x(),
                                                eq_emit_y=bunch.epsn_y(),
                                                damping_time_x_turns=TAU_X*OMEGA_REV/(2*np.pi),
                                                damping_time_y_turns=TAU_Y*OMEGA_REV/(2*np.pi),
                                                beta_x=BETA_X_SMOOTH,
                                                beta_y=BETA_Y_SMOOTH)
    synchr_rad_long = SynchrotronRadiationLongitudinal(eq_sig_dp=SIGMA_DP, damping_time_z_turns=TAU_Z*OMEGA_REV/(2*np.pi), E_loss_eV=e*U_LOSS )
    

    slice_monitor = SliceMonitor(filename='htmonitor',
                                 n_steps=n_turns,
                                 slicer=wake_slicer,
                                 parameters_dict=None,
                                 write_buffer_every=512,
                                 buffer_size=4096,)
    chroma = Chromaticity(Qp_x=[0], Qp_y=[0])
    trans_map = TransverseMap(s, alpha_x, beta_x, D_x,
                              alpha_y, beta_y, D_y, Q_X, Q_Y, [chroma])
    trans_one_turn = [m for m in trans_map]
    map_ = trans_one_turn + [long_map, wake_field, synchr_rad_long]
    for turn in tqdm(range(n_turns)):
        for m_ in map_:
            m_.track(bunch)
        slice_monitor.dump(bunch)
        
if __name__ == "__main__":
    