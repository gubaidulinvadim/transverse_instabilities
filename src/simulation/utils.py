import argparse

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
        help="Flag to include quadrupolar wakes. Defaults to 'False'.",
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

