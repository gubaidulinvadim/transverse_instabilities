from submission import write_submission_script_ccrt, write_submission_script_slurm
import argparse
from utils import get_parser_for_single_bunch
import numpy as np
import os
MOUNT_FOLDER = '/ccc/work/cont003/soleil/gubaiduv/mbtrack2_transverse_instabilities:/home/dockeruser/mbtrack2_transverse_instabilities'
IMAGE_NAME = 'mbtrack2'
SCRIPT_NAME = 'mbtrack2_transverse_instabilities/track_TI.py'

if __name__ == "__main__":
    parser = get_parser_for_single_bunch()
    parser.add_argument('--job_name', action='store', metavar='JOB_NAME', type=str, default='current_scan',
                        help='Name of the job and associated .our and .err files. Defaults to "current_scan"')
    parser.add_argument('--job_time', action='store', metavar='TIMELIMIT', type=str, default='100000',
                        help='Timelimit as a str for jobs on ccrt or slurm. Defaults to "100000"')
    parser.add_argument('--sub_mode', action='store', metavar='SUB_MODE', type=str, default='ccrt',
                        help='Submission mode. Accepted values are ["local", "ccrt", "slurm"], defaults to "ccrt"')
    parser.add_argument('--max_current', action='store', metavar='MAX_CHROM', type=float, default=3.0,
                        help="Maximal current value for bunch current scan. Defaults to 10.0.")
    parser.add_argument('--min_current', action='store', metavar='MIN_CHROM', type=float, default=0.5,
                        help="Maximal current value for bunch current scan. Defaults to 0.01.")
    parser.add_argument('--n_scan_points', action='store', metavar='N_SCAN_POINTS', type=int, default=30,
                        help='Number of bunch current value to be scanned. Each point is a separate job! Defaults to 30.')
    args = parser.parse_args()
    if args.sub_mode == 'ccrt':
        for i, I_b in enumerate(1e-3*np.linspace(args.min_current, args.max_current, args.n_scan_points)):
            job = write_submission_script_ccrt(args.job_name+''.format(i),
                                               args.job_time,
                                               args.n_macroparticles,
                                               args.n_turns,
                                               args.n_bin,
                                               I_b,
                                               args.Qp_x,
                                               args.Qp_y,
                                               args.ID_state,
                                               args.include_Zlong,
                                               args.harmonic_cavity)
            os.system('ccc_msub {:}'.format(job))
            os.system('rm -r {:}'.format(job))

    else:
        pass
