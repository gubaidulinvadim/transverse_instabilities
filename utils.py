import argparse
def get_parser_for_single_bunch():
    parser = argparse.ArgumentParser(
        description="A script to track transverse instabilities in a light source storage ring.")
    parser.add_argument('--n_macroparticles', action='store', metavar='N_MACRO', type=int,
                        default=int(1e6), help='Number of electron macroparticles in a bunch')
    parser.add_argument('--n_turns', action='store', metavar='N_TURNS', type=int,
                        default=int(5e4), help='Number of turns for tracking')
    parser.add_argument('--n_bin', action='store', metavar='N_BIN', type=int,
                        default=100, help='Number of bins for wakepotential tracking')
    parser.add_argument('--bunch_current', action='store', metavar='I_BUNCH', type=float,
                        default=1.2e-3, help='Single-bunch current in A')
    parser.add_argument('--Qp_x', action='store', metavar='QP_X', type=float,
                        default=1.6, help='Horizontal chromaticity (absolute)')
    parser.add_argument('--Qp_y', action='store', metavar='QP_Y', type=float,
                        default=1.6, help='Vertical chromaticity (absolute)')
    parser.add_argument('--ID_state', action='store', help='A flag for open or closed IDs',
                        type=str, default='open',)
    return parser
                        