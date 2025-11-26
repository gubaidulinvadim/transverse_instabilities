"""
Deprecated utility functions for submission scripts.

This module is deprecated. The parser functions are now available in
src/simulation/utils.py which should be used instead.
"""

import argparse
import warnings

warnings.warn(
    "submission/utils.py is deprecated. Please use simulation/utils.py instead.",
    DeprecationWarning,
    stacklevel=2
)

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
    parser.add_argument(
        "--ibs",
        action="store",
        help="Flag to include intrabeam scattering. Defaults to 'False'.",
        default='False',
        type=str)
    parser.add_argument(
        "--quad",
        action="store",
        help="Flag to include quadrupolar wake. Defaults to 'False'.",
        default='False',
        type=str)
    parser.add_argument(
        "--wake_y",
        action="store",
        help="Flag to include vertical wake, if False horizontal wake is included instead. Defaults to 'False'.",
        default='True',
        type=str)
    return parser

def get_parser_for_multibunch():
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
    return parser

def laguerre_fit(x, *coeffs):
    from scipy.special import genlaguerre
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
    # from scipy.optimize import curve_fit
    # from sklearn.metrics import r2_score
    order = 4
    r2 = 0
    while r2 < 0.998 and order != 20:
        p0 = np.zeros(shape=(order, ))
        p0[0:3] = 0.5, 0.5, 1
        popt, pcov = curve_fit(laguerre_fit, t0, data, p0=p0)
        r2 = r2_score(data, laguerre_fit(t0, *popt))
        order += 1
    return r2, popt
