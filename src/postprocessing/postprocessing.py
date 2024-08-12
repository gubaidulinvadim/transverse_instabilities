import h5py as hp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PyNAFF as pnf
from FITX import fit_risetime
from machine_data.TDR2 import *
from scipy.constants import c
from scipy.signal import find_peaks, periodogram
from SOLEILII_parameters.SOLEILII_TDR_parameters import *
from tqdm.notebook import tqdm

FOLDER = '/home/gubaidulin/scripts/tracking/transverse_instabilities/data/raw/sbi/'
FOLDER_FIG = '/home/gubaidulin/scripts/tracking/transverse_instabilities/data/processed/'


def plot_Q_s(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fftz = np.abs(np.fft.rfft(m[4, :]))
    fftfreqz = np.fft.rfftfreq(m[4, :].shape[0])

    fig, ax = plt.subplots(1, 1)
    ax.plot(fftfreqz, fftz, marker='.')
    ax.set_xlim(0, 5e-3)
    ax.axvline(Q_S)
    ax.set_ylabel('Spectrum power (arb. units)')
    ax.set_xlabel('Synchrotron tune, $Q_s$')
    plt.savefig(
        FOLDER_FIG +
        'synchrotron_tune(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()

def plot_offset(ax,
                m,
                mp,
                std,
                n_macroparticles,
                n_turns,
                n_bin,
                bunch_current,
                Qp_x,
                Qp_y,
                n_bunches=416,
                n_sampling=1,
                **matplotlib_kwargs):
    turns = np.linspace(0, len(m) / n_bunches * n_sampling, len(m))
    ax.plot(turns, m / std, **matplotlib_kwargs)
    min_level = 0.15
    m = np.trim_zeros(m, trim='b')
    mp = np.trim_zeros(mp, trim='b')
    # m = m[:50_000]
    # mp = mp[:50_000]
    
    # m = m[abs(m) < 10000]
    # mp = mp[abs(m) < 10000]
    signal = np.sqrt(
        m**2 +
        (BETA_Y_SMOOTH * mp)**2) / std
    smoothing_window_size = 100
    risetime = fit_risetime(
        signal,
        min_level=min_level,
        smoothing_window_size=smoothing_window_size,
        # until=45_000,
        matplotlib_axis=None)
    risetime /= n_bunches
    risetime *= n_sampling
    ax.set_xlabel('Time (turns)')
    ax.set_ylabel('Bunch c.\,m. offset, $\langle y \\rangle/\sigma_y$')
    ax.set_xlim(0, )
    try:
        ax.title.set_text('Risetime of {:} turns'.format(int(risetime)))
    except:
        ax.title.set_text('Risetime of {:} turns'.format(risetime))
    plt.savefig(
        FOLDER_FIG +
        'beam_offset(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()
    return risetime


def post_mwi(m, std, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x,
             Qp_y):
    fig, ax = plt.subplots(1, 1)
    ax.plot(std[5, :] * 100)
    ax.set_xlabel('Turns (time)')
    ax.set_ylabel('Energy offset, $\sigma_\delta$ (\%)')
    ax.title.set_text('Energy offset, $I_b={:.1f}$ (mA)'.format(bunch_current *
                                                                1e3))
    plt.savefig(
        FOLDER_FIG +
        'energy_offset(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()
    final_energy_offset = np.nanmean(
        np.trim_zeros(std[5, :], trim='b')[-5000:])
    max_energy_offset = np.nanmax(np.trim_zeros(std[5, :], trim='b')[-5000:])
    min_energy_offset = np.nanmin(np.trim_zeros(std[5, :], trim='b')[-5000:])
    return final_energy_offset, max_energy_offset, min_energy_offset


def post_bunch_length(m, std, n_macroparticles, n_turns, n_bin, bunch_current,
                      Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    ax.plot(std[4, :] / 1e-12)
    ax.set_xlabel('Turns (time)')
    ax.set_ylabel('Bunch length, $\sigma_z$ (ps)')
    ax.title.set_text('Bunch length, $I_b={:.1f}$ (mA)'.format(bunch_current *
                                                               1e3))
    plt.savefig(
        FOLDER_FIG +
        'bunch_length(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()
    final_bunch_length = np.nanmean(
        np.trim_zeros(std[4, :], trim='b')[-10000:])
    return final_bunch_length


def plot_Qb(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    fftfreqy, ffty = periodogram(m[2, :], )
    ax.plot(fftfreqy, ffty)
    multiple_of = 5
    ax.set_xlabel('Coherent frequency, $\omega/\omega_0$')
    ax.set_ylabel('Spectrum power (arb.\,units)')
    ax.set_xlim(Q_Y - np.floor(Q_Y) - multiple_of * Q_S,
                Q_Y - np.floor(Q_Y) + multiple_of * Q_S)
    ax.set_xticks(
        np.linspace(Q_Y - np.floor(Q_Y) - multiple_of * Q_S,
                    Q_Y - np.floor(Q_Y) + multiple_of * Q_S,
                    2 * multiple_of + 1))
    labels = ['$Q_y-Q_s$', '$Q_y$', '$Q_y+Q_s$']
    for i in range(2, multiple_of + 1):
        labels.insert(0, '$Q_y-{:}Q_s$'.format(i))
        labels.append('$Q_y+{:}Q_s$'.format(i))
    ax.set_xticklabels(labels, rotation=20)
    # ax.title.set_text('Coherent betatron tune')
    ax.xaxis.grid(True)
    plt.savefig(
        FOLDER_FIG +
        'coherent_betatron_tune(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()
    # peaks = find_peaks(ffty / np.max(ffty), height=0.1, distance=20)[0]
    # naff_res = pnf.naff(m[2,:], turns=m[2,:].shape[0], nterms=50, skipTurns=0, getFullSpectrum=False, window=1)
    return fftfreqy, ffty #fftfreqy[peaks], ffty[peaks] / np.max(ffty)



def plot_intrabunch(dip_y, tau_y, profile_y, n_macroparticles, n_turns, n_bin,
                    bunch_current, Qp_x, Qp_y):
    fig, ax = plt.subplots(1, 1)
    linenumber = 50
    linestart = 44950
    lineend = 45000

    ax.plot((tau_y[:, linestart:lineend]) * c / SIGMA_Z,
            dip_y[:, linestart:lineend] * profile_y[:, linestart:lineend],
            color='black',
            alpha=0.5)
    ax.set_xlim(-3, 3)
    ax.set_xlabel('Longitudinal position, $z/\sigma_z$')
    ax.set_ylabel('Dipole moment (arb. units)')
    ax.title.set_text(
        'Intrabunch motion for last {:} turns, N_m={:.1e}'.format(
            linenumber, n_macroparticles))
    plt.savefig(
        FOLDER_FIG +
        'intrabunch_motion(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f}).pdf'
        .format(n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y))
    plt.close()


def post_single(n_macroparticles=1e6,
                n_turns=5e4,
                n_bin=100,
                bunch_current=1.2e-3,
                Qp_x=1.6,
                Qp_y=1.6,
                ID_state='open',
                Zlong='False',
                cavity='False',
                max_kick=0.0,
                sc='False'):
    filename = FOLDER + 'monitors(n_mp={:.1e},n_turns={:.1e},n_bin={:},bunch_current={:.1e},Qp_x={:.2f},Qp_y={:.2f},id_state={},Zlong={},cavity={:},max_kick={:.1e},sc={:})'.format(
        n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y, ID_state,
        Zlong, cavity, max_kick, sc)
    with hp.File(filename + '.hdf5') as f:
        m = f['BunchData_0']['mean'][:]
        std = f['BunchData_0']['std'][:]
        J = f['BunchData_0']['cs_invariant'][:]
        emit = f['BunchData_0']['emit'][:]

    plot_Q_s(m, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    fig, ax = plt.subplots(1, 1)

    y = np.trim_zeros(m[2, :], trim='b')
    yp = np.trim_zeros(m[3, :], trim='b')

    yp = yp[np.abs(y) < 1e10]
    y = y[np.abs(y) < 1e10]

    risetime = plot_offset(ax,
                           y,
                           yp,
                           std[2, 0],
                           n_macroparticles,
                           n_turns,
                           n_bin,
                           bunch_current,
                           Qp_x,
                           Qp_y,
                           n_bunches=1,
                           n_sampling=1)

    peak_freqs, peak_amps = plot_Qb(m, n_macroparticles, n_turns, n_bin,
                                    bunch_current, Qp_x, Qp_y)
    final_energy_offset, max_energy_offset, min_energy_offset = post_mwi(
        m, std, n_macroparticles, n_turns, n_bin, bunch_current, Qp_x, Qp_y)
    final_bunch_length = post_bunch_length(m, std, n_macroparticles, n_turns,
                                           n_bin, bunch_current, Qp_x, Qp_y)
    with hp.File(filename + '.hdf5') as f:
        dip_y = f['WakePotentialData_0']['dipole_Wydip'][:]
        profile_y = f['WakePotentialData_0']['profile_Wydip'][:]
        tau_y = f['WakePotentialData_0']['tau_Wydip'][:]
    plot_intrabunch(dip_y, tau_y, profile_y, n_macroparticles, n_turns, n_bin,
                    bunch_current, Qp_x, Qp_y)
    return risetime, peak_freqs, peak_amps, final_energy_offset, max_energy_offset, min_energy_offset, final_bunch_length


def post_tmci_mwi_bunch_length(n_macroparticles=1e6,
                               n_turns=5e4,
                               n_bin=100,
                               bunch_current_min=.1e-3,
                               bunch_current_max=5e-3,
                               n_points=50):
    bunch_currents = np.linspace(bunch_current_min, bunch_current_max,
                                 n_points)
    results = pd.DataFrame(columns=[
        'BunchCurrent', 'Risetime', 'PeakFreqs', 'PeakAmps',
        'FinalEnergyOffset', 'MaxEnergyOffset', 'MinEnergyOffset',
        'FinalBunchLength'
    ])
    for bunch_current in bunch_currents:
        try:
            risetime, peak_freqs, peak_amps, final_energy_offset, max_energy_offset, min_energy_offset, final_bunch_length = post_single(
                n_macroparticles=n_macroparticles,
                n_turns=n_turns,
                n_bin=n_bin,
                bunch_current=bunch_current,
                Qp_x=0,
                Qp_y=0)
        except:
            risetime, peak_freqs, peak_amps, final_energy_offset, max_energy_offset, min_energy_offset, final_bunch_length = np.NAN, [
                np.NAN
            ], [np.NAN], np.NAN, np.NAN, np.NAN, np.NAN
        result = pd.DataFrame(
            {
                'BunchCurrent': bunch_current,
                'Risetime': risetime,
                'PeakFreqs': peak_freqs[0],
                'PeakAmps': peak_amps[0],
                'FinalEnergyOffset': final_energy_offset,
                'MaxEnergyOffset': max_energy_offset,
                'MinEnergyOffset': min_energy_offset,
                'FinalBunchLength': final_bunch_length
            },
            index=[0])

        results = pd.concat([results, result], ignore_index=True)

    fig, ax = plt.subplots(1, 1)
    ax.plot(bunch_currents / 1e-3,
            2 * pi / results['Risetime'][:] / Q_S,
            marker='.',
            linewidth=0)
    # ax.axhline(2*pi/(ring.tau[2]*ring.f0)/Q_S, color='gray', linestyle='solid', label='Radiation damping')
    ax.set_xlim(0, )
    ax.set_ylim(0, )
    ax.title.set_text('TMCI growth rate')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Instability growth rate, $\mathrm{Im}\Delta Q/Q_s$')
    plt.savefig(FOLDER_FIG + 'tmci.pdf')
    plt.close()

    fig, ax = plt.subplots(1, 1)
    ax.plot(bunch_currents * 1e3,
            results['FinalBunchLength'][:] / 1e-12,
            marker='.')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Bunch length, $\sigma_z$ (ps)')
    ax.title.set_text('Bunch lengthening')
    plt.savefig(FOLDER_FIG + 'bunch_lengthening.pdf')
    plt.close()

    fig, ax = plt.subplots(1, 1)
    sigmas_dp = results['FinalEnergyOffset'][:]
    ax.plot(bunch_currents * 1e3, np.array(sigmas_dp) * 1e2, marker='.')
    ax.title.set_text('MWI threshold')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Energy offset, $\sigma_\delta$ (\%)')
    plt.savefig(FOLDER_FIG + 'mwi.pdf')
    plt.close()
    return results


def post_bunch_current_scan(n_macroparticles=1e6,
                            n_turns=5e4,
                            n_bin=100,
                            bunch_current_min=.1e-3,
                            bunch_current_max=5e-3,
                            n_points=50):
    bunch_currents = np.linspace(bunch_current_min, bunch_current_max,
                                 n_points)
    results = pd.DataFrame(columns=[
        'BunchCurrent', 'Risetime', 'PeakFreqs', 'PeakAmps',
        'FinalEnergyOffset', 'MaxEnergyOffset', 'MinEnergyOffset',
        'FinalBunchLength'
    ])
    for bunch_current in bunch_currents:
        try:
            risetime, peak_freqs, peak_amps, final_energy_offset, max_energy_offset, min_energy_offset, final_bunch_length = post_single(
                n_macroparticles=n_macroparticles,
                n_turns=n_turns,
                n_bin=n_bin,
                bunch_current=bunch_current,
                Qp_x=1.2,
                Qp_y=1.2)
        except:
            risetime, peak_freqs, peak_amps, final_energy_offset, max_energy_offset, min_energy_offset, final_bunch_length = np.NAN, [
                np.NAN
            ], [np.NAN], np.NAN, np.NAN, np.NAN, np.NAN
        result = pd.DataFrame(
            {
                'BunchCurrent': bunch_current,
                'Risetime': risetime,
                'PeakFreqs': peak_freqs[0],
                'PeakAmps': peak_amps[0],
                'FinalEnergyOffset': final_energy_offset,
                'MaxEnergyOffset': max_energy_offset,
                'MinEnergyOffset': min_energy_offset,
                'FinalBunchLength': final_bunch_length
            },
            index=[0])

        results = pd.concat([results, result], ignore_index=True)

    fig, ax = plt.subplots(1, 1)
    ax.plot(bunch_currents / 1e-3,
            2 * pi / results['Risetime'][:] / Q_S,
            marker='.',
            linewidth=0)
    # ax.axhline(2*pi/(ring.tau[2]*ring.f0)/Q_S, color='gray', linestyle='solid', label='Radiation damping')
    ax.set_xlim(0, )
    ax.set_ylim(0, )
    ax.title.set_text('Head-tail growth rate')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Instability growth rate, $\mathrm{Im}\Delta Q/Q_s$')
    plt.savefig(FOLDER_FIG + 'tmci.pdf')
    plt.close()

    fig, ax = plt.subplots(1, 1)
    ax.plot(bunch_currents * 1e3,
            results['FinalBunchLength'][:] / 1e-12,
            marker='.')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Bunch length, $\sigma_z$ (ps)')
    ax.title.set_text('Bunch lengthening')
    plt.savefig(FOLDER_FIG + 'bunch_lengthening.pdf')
    plt.close()

    fig, ax = plt.subplots(1, 1)
    sigmas_dp = results['FinalEnergyOffset'][:]
    ax.plot(bunch_currents * 1e3, np.array(sigmas_dp) * 1e2, marker='.')
    ax.title.set_text('MWI threshold')
    ax.set_xlabel('Bunch current, $I_b$ (mA)')
    ax.set_ylabel('Energy offset, $\sigma_\delta$ (\%)')
    plt.savefig(FOLDER_FIG + 'mwi.pdf')
    plt.close()
    return results


if __name__ == "__main__":
    n_macroparticles = 1e6
