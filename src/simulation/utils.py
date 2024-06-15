import argparse

import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
# from sklearn.metrics import r2_score
import numpy as np
from machine_data import v2366_v3
from mbtrack2 import BeamLoadingEquilibrium, CavityResonator
from scipy.special import genlaguerre


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


def get_parser_for_single_bunch():
    parser = argparse.ArgumentParser(
        description=
        "A script to track transverse instabilities in a light source storage ring."
    )
    parser.add_argument(
        "--n_macroparticles",
        action="store",
        metavar="N_MACRO",
        type=int,
        default=int(1e6),
        help="Number of electron macroparticles in a bunch",
    )
    parser.add_argument(
        "--n_turns",
        action="store",
        metavar="N_TURNS",
        type=int,
        default=int(5e4),
        help="Number of turns for tracking",
    )
    parser.add_argument(
        "--n_bin",
        action="store",
        metavar="N_BIN",
        type=int,
        default=100,
        help="Number of bins for wakepotential tracking",
    )
    parser.add_argument(
        "--bunch_current",
        action="store",
        metavar="I_BUNCH",
        type=float,
        default=1.2e-3,
        help="Single-bunch current in A",
    )
    parser.add_argument(
        "--Qp_x",
        action="store",
        metavar="QP_X",
        type=float,
        default=1.6,
        help="Horizontal chromaticity (absolute)",
    )
    parser.add_argument(
        "--Qp_y",
        action="store",
        metavar="QP_Y",
        type=float,
        default=1.6,
        help="Vertical chromaticity (absolute)",
    )
    parser.add_argument(
        "--id_state",
        action="store",
        help="A flag for open or closed IDs",
        type=str,
        default="open",
    )
    parser.add_argument(
        "--include_Zlong",
        action="store",
        help=
        "A flag to include longitudinal wakefield into tracking (for bunch lenghtening).",
        type=str,
        default="False",
    )
    parser.add_argument(
        "--harmonic_cavity",
        action="store",
        help='A flag for harmonic cavity. Defaults to "False".',
        default="False",
        type=str,
    )
    parser.add_argument(
        "--max_kick",
        action="store",
        help='Max kick for feedback in rad.',
        default=1.6e-6,
        type=float,
    )
    parser.add_argument(
        "--sc",
        action="store",
        help="Flag to include space-charge force. Defaults to 'False'.",
        default='False',
        type=str)
    return parser


def laguerre_fit(x, *coeffs):
    a = coeffs[0]
    b = coeffs[1]
    c = coeffs[2]
    orders = np.linspace(0, len(coeffs) - 4, len(coeffs) - 3, dtype=np.int64)
    laguerres = np.array([
        coeffs[3 + order] * genlaguerre(order, 0)(b * (x + c)**2)
        for order in orders
    ])
    return np.exp(-a * (x + c)**2) * np.sum(laguerres, axis=0)


def fit_loop(t0, data):
    order = 4
    r2 = 0
    while r2 < 0.998 and order != 20:
        p0 = np.zeros(shape=(order, ))
        p0[0:3] = 0.5, 0.5, 1
        popt, pcov = curve_fit(laguerre_fit, t0, data, p0=p0)
        r2 = r2_score(data, laguerre_fit(t0, *popt))
        order += 1
    return r2, popt
