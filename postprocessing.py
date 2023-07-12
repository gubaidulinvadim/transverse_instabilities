import numpy as np
from scipy.constants import c
from tqdm.notebook import tqdm
import h5py as hp
import matplotlib.pyplot as plt
from aps_figures.aps_one_column import *
from FITX import fit_risetime
from machine_data.TDR2 import *
from SOLEILII_parameters.SOLEILII_TDR_parameters import *

FOLDER = '/home/gubaidulin/scripts/tracking/Results/IDsopen/chroma_scan200x32/'
FOLDER_FIG = '/home/gubaidulin/scripts/tracking/Figures/IDsopen/chroma_scan200x32/'
#    Qmin=0.01, Qmax,=5.0, n_points=50, plane='y'
#         if plane=='y':
#         Qp_y = np.linspace(Qmin, Qmax, n_points)
#     elif plane=='x':
#         Qp_x = np.linspace(Qmin, Qmax, n_points)    
    
def plot_Q_s(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fftz = np.abs(np.fft.rfft(m[4,:]))
    fftfreqz = np.fft.rfftfreq(m[4,:].shape[0])
    
    fig, ax = plt.subplots(1, 1)
    ax.plot(fftfreqz, fftz, marker='.')
    ax.set_xlim(0, 5e-3)
    ax.axvline(Q_S)
    ax.set_ylabel('Spectrum power (arb. units)')
    ax.set_xlabel('Synchrotron tune, $Q_s$')
    plt.savefig(FOLDER_FIG+'synchrotron_tune(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'.format(n_macroparticles,
                                                                                                                        n_turns, 
                                                                                                                        n_bin,
                                                                                                                        bunch_current, 
                                                                                                                        Qp_x,
                                                                                                                        Qp_y))
    plt.close()

def plot_offset(m, std, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    ax.plot(m[2,:]/std[2, 0])
    min_level = 0.05
    signal = np.sqrt(m[2,:]**2+(BETA_Y_SMOOTH*m[3,:])**2)/std[2,0]
    smoothing_window_size = 50
    risetime = fit_risetime(signal,
                          min_level=min_level, 
                          smoothing_window_size=smoothing_window_size,
                          matplotlib_axis=ax)
    ax.set_xlabel('Time (turns)')
    ax.set_ylabel('Bunch c.\,m. offset, $\langle y \\rangle/\sigma_y$')
    ax.set_xlim(0, )
    try:
        ax.title.set_text('Risetime of {:} turns'.format(int(risetime)))
    except:
        ax.title.set_text('Risetime of {:} turns'.format(risetime))
    plt.savefig(FOLDER_FIG+'beam_offset(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'.format(n_macroparticles,
                                                                                                                        n_turns, 
                                                                                                                        n_bin,
                                                                                                                        bunch_current, 
                                                                                                                        Qp_x,
                                                                                                                        Qp_y))
    plt.close()
    return risetime

def plot_Qb(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    ffty = np.abs(np.fft.rfft(m[2,:]))
    fftfreqy = np.fft.rfftfreq(m[2,:].shape[0])
    ax.plot(fftfreqy, ffty)
    multiple_of = 5
    ax.set_xlabel('Coherent frequency, $\omega/\omega_0$')
    ax.set_ylabel('Spectrum power (arb.\,units)')
    ax.set_xlim(Q_Y-np.floor(Q_Y)-multiple_of*Q_S, Q_Y-np.floor(Q_Y)+multiple_of*Q_S)
    ax.set_xticks(np.linspace(Q_Y-np.floor(Q_Y)-multiple_of*Q_S, Q_Y-np.floor(Q_Y)+multiple_of*Q_S, 2*multiple_of+1))
    labels = ['$Q_y-Q_s$', '$Q_y$', '$Q_y+Q_s$']
    for i in range(2, multiple_of+1):
        labels.insert(0, '$Q_y-{:}Q_s$'.format(i))
        labels.append('$Q_y+{:}Q_s$'.format(i))
    ax.set_xticklabels(labels, rotation = 20)
    # ax.title.set_text('Coherent betatron tune')
    ax.xaxis.grid(True)
    plt.savefig(FOLDER_FIG+'coherent_betatron_tune(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'.format(n_macroparticles,
                                                                                                                        n_turns, 
                                                                                                                        n_bin,
                                                                                                                        bunch_current, 
                                                                                                                        Qp_x,
                                                                                                                        Qp_y))
    plt.close()
def plot_intrabunch(dip_y, tau_y, profile_y,  n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    linenumber = 50
    linestart = 44950 
    lineend =45000
    # ax.plot((tau_y[:,-linenumber:])*c/SIGMA_Z, profile_y[:,-linenumber:], color='black', alpha=0.5)

    ax.plot((tau_y[:,linestart:lineend])*c/SIGMA_Z, dip_y[:,linestart:lineend]*profile_y[:,linestart:lineend], color='black', alpha=0.5)
    ax.set_xlim(-3, 3)
    ax.set_xlabel('Longitudinal position, $z/\sigma_z$')
    ax.set_ylabel('Dipole moment (arb. units)')
    ax.title.set_text('Intrabunch motion for last {:} turns, N_m={:.1e}'.format(linenumber, n_macroparticles))
    plt.savefig(FOLDER_FIG+'intrabunch_motion(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'.format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()
def post_single(n_macroparticles=1e6, n_turns=5e4, n_bin=100, bunch_current=1.2e-3, Qp_x = 1.6, Qp_y=1.6, ):
    filename = FOLDER+'monitors(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f})'.format(
                                                                                                                        n_macroparticles,
                                                                                                                        n_turns, 
                                                                                                                        n_bin,
                                                                                                                        bunch_current, 
                                                                                                                        Qp_x,
                                                                                                                        Qp_y)
    with hp.File(filename+'.hdf5') as f:
        m = f['BunchData_0']['mean'][:]
        std = f['BunchData_0']['std'][:]
        J = f['BunchData_0']['cs_invariant'][:]
        emit = f['BunchData_0']['emit'][:]
    
    plot_Q_s(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    
    risetime = plot_offset(m, std, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    
    plot_Qb(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    
    with hp.File(filename+'.hdf5') as f:
        dip_y = f['WakePotentialData_0']['dipole_Wydip'][:]

        profile_y = f['WakePotentialData_0']['profile_Wydip'][:]
        tau_y = f['WakePotentialData_0']['tau_Wydip'][:]
    plot_intrabunch(dip_y, tau_y, profile_y,  n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    return risetime
def plot_tmci(n_macroparticles=1e6, n_turns=5e4, n_bin=100, bunch_current=1.2e-3):
    
if __name__=="__main__":
    n_macroparticles = 1e6
    