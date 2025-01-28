import matplotlib.pyplot as plt
import numpy as np
from mbtrack2 import BeamLoadingEquilibrium, CavityResonator
from mbtrack2.tracking.feedback import ExponentialDamper, FIRDamper
from mbtrack2.impedance.wakefield import WakeField
from machine_data.TDR2 import *
from mbtrack2.tracking import (RFCavity, WakePotential)

def setup_wakes(ring, id_state, include_Zlong, n_bin):
    wakemodel = load_TDR2_wf(version=("TDR2.1_ID" + id_state+"_pandas2"))
    
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
    return wakefield_tr, wakefield_long, wakemodel


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


def get_active_cavity_params(ring):
    I0 = 0.2
    xi = 1.1
    Vc = 1.7e6

    HC = CavityResonator(ring,
                         m=4,
                         Rs=60 * 31e3,
                         Q=31e3,
                         QL=31e3,
                         detune=1e6,
                         Ncav=1)
    HC.Vg = 0
    HC.theta_g = 0

    HC_det = I0 * HC.Rs / HC.Q * ring.f1 / Vc * HC.m**2 / xi
    HC.detune = HC_det

    delta = HC.Vb(I0) * np.cos(HC.psi)

    MC = CavityResonator(ring,
                         m=1,
                         Rs=5e6,
                         Q=35.7e3,
                         QL=6e3,
                         detune=1e6,
                         Ncav=4)
    MC.Vc = Vc
    MC.theta = np.arccos((ring.U0 + delta) / MC.Vc)
    MC.set_optimal_detune(I0)
    MC.set_generator(I0)

    BLE = BeamLoadingEquilibrium(ring, [MC, HC], I0, auto_set_MC_theta=True)
    BLE.beam_equilibrium(CM=True, plot=False)
    print(BLE.std_rho() / 3e8 * 1e12)

    print("Form factors", BLE.F, BLE.PHI)

    for i, cavity in enumerate([MC, HC]):
        Vc_phasor = -1 * cavity.Vb(I0) * BLE.F[i] * np.exp(1j * (
            cavity.psi - BLE.PHI[i])) + cavity.Vg * np.exp(1j * cavity.theta_g)
        cavity.Vc = np.abs(Vc_phasor)
        cavity.theta = np.angle(Vc_phasor)

    return MC.Vc, MC.theta, HC.Vc, HC.theta


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


def setup_dual_rf(ring, beam, harmonic_cavity, bunch_current, wakemodel):
    Vc = 1.7e6
    if harmonic_cavity == "True":
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
    else:
        rf = RFCavity(ring, m=1, Vc=Vc, theta=np.arccos(ring.U0 / Vc))
        hrf = None
    return rf, hrf
