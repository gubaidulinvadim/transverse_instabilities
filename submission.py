import os
import argparse
from utils import get_parser_for_single_bunch
IMAGE_NAME = 'mbtrack2'
SCRIPT_NAME = 'mbtrack2_transverse_instabilities/track_TI.py'

def write_submission_script_ccrt(job_name, job_time, n_macroparticles=int(1e6), n_turns=int(5e4), n_bin=100, bunch_current=1e-3, Qp_x=1.6, Qp_y=1.6, ID_state='open', include_Zlong=False):
    mount_folder = '/ccc/work/cont003/soleil/gubaiduv/mbtrack2_transverse_instabilities:/home/dockeruser/mbtrack2_transverse_instabilities'
    with open(job_name, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("#MSUB -m work,scratch\n")
        f.write("#MSUB -q milan\n")
        f.write("#MSUB -n 1\n")
        f.write("#MSUB -c 8\n")
        f.write("#MSUB -T {:}\n".format(job_time))
        f.write("#MSUB -A soleil\n")
        f.write("#MSUB -@ gubaidulinvadim@gmail.com:begin,end,requeue\n")
        f.write(
            "#MSUB -o /ccc/cont003/home/soleil/gubaiduv/{0:}_%I.err\n".format(job_name))
        f.write(
            "#MSUB -e /ccc/cont003/home/soleil/gubaiduv/{0:}_%I.out\n".format(job_name))
        f.write(
            "pcocc run --mount {0:}  -I {1:} --entry-point -- python {2:} --n_macroparticles {3:} --n_turns {4:} --n_bin {5:} --bunch_current {6:} --Qp_x {7:} --Qp_y {8:} --ID_state {9:} --include_Zlong {10:}\n".format(mount_folder,
                                                                                                                                                                    IMAGE_NAME,
                                                                                                                                                                    SCRIPT_NAME,
                                                                                                                                                                    n_macroparticles,
                                                                                                                                                                    n_turns,
                                                                                                                                                                    n_bin,
                                                                                                                                                                    bunch_current, 
                                                                                                                                                                    Qp_x,
                                                                                                                                                                    Qp_y,
                                                                                                                                                                    ID_state,
                                                                                                                                                                    include_Zlong))
    return job_name


def write_submission_script_slurm(job_name, job_time, n_macroparticles=int(1e6), n_turns=int(5e4), n_bin=100, bunch_current=1e-3, Qp_x=1.6, Qp_y=1.6, ID_state='open', include_Zlong=False):
    with open(job_name, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("#SBATCH --partition sumo\n")
        f.write("#SBATCH -n 8\n")
        f.write("#SBATCH --time={:}\n".format(job_time))
        f.write('#SBATCH --export=ALL\n')
        f.write("#SBATCH --mail-user='gubaidulinvadim@gmail.com'\n")
        f.write('#SBATCH --mail-type=begin,end,requeue\n')
        f.write(
            "#SBATCH --error=/home/sources/physmach/gubaidulin/err/{0:}_%I.err\n".format(job_name))
        f.write('module load tools/singularity/current\n')
        f.write(
            "singularity exec --no-home --B {0:} {1:} python {2:} --n_macroparticles {3:} --n_turns {4:} --n_bin {5:} --bunch_current {6:} --Qp_x {7:} --Qp_y {8:} --ID_state {9:} --include_Zlong {10:}\n".format(MOUNT_FOLDER,
                                                                                                                                                                    IMAGE_NAME,
                                                                                                                                                                    SCRIPT_NAME,
                                                                                                                                                                    n_macroparticles,
                                                                                                                                                                    n_turns,
                                                                                                                                                                    n_bin,
                                                                                                                                                                    bunch_current, 
                                                                                                                                                                    Qp_x,
                                                                                                                                                                    Qp_y,
                                                                                                                                                                    ID_state,
                                                                                                                                                                    include_Zlong))
    return job_name


if __name__ == '__main__':
    parser = get_parser_for_single_bunch()
    parser.add_argument('--job_name', action='store', metavar='JOB_NAME', type=str, default='job',
                        help='Name of the job and associated .our and .err files. Defaults to "job"')
    parser.add_argument('--job_time', action='store', metavar='TIMELIMIT', type=str, default='100000',
                        help='Timelimit as a str for jobs on ccrt or slurm. Defaults to "100000"')
    parser.add_argument('--sub_mode', action='store', metavar='SUB_MODE', type=str, default='ccrt',
                        help='Submission mode. Accepted values are ["local", "ccrt", "slurm"], defaults to "ccrt"')
    args = parser.parse_args()
    if args.sub_mode == 'ccrt':
        
        job = write_submission_script_ccrt(args.job_name,
                                args.job_time,
                                args.n_macroparticles,
                                args.n_turns,
                                args.n_bin,
                                args.bunch_current,
                                args.Qp_x,
                                args.Qp_y,
                                args.ID_state,
                                args.include_Zlong)
        os.system('ccc_msub {:}'.format(job))
    elif args.sub_mode == 'slurm': 
        job = write_submission_script_ccrt(args.job_name,
                                args.job_time,
                                args.n_macroparticles,
                                args.n_turns,
                                args.n_bin,
                                args.bunch_current,
                                args.Qp_x,
                                args.Qp_y, 
                                args.ID_state,
                                args.include_Zlong)
        os.system('sbatch {:}'.format(job))
    else:
        pass
    os.system('rm -r {:}'.format(job))
