import argparse
import os, sys

from utils import get_parser_for_single_bunch


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, max_kick, sc, ibs):
    command_string = (f"/home/dockeruser/venv/bin/python3 {script_name:}" +
                      f" --n_macroparticles {n_macroparticles:}" +
                      f" --n_turns {n_turns:}" + f" --n_bin {n_bin:}" +
                      f" --bunch_current {bunch_current:}" +
                      f" --Qp_x {Qp_x:}" + f" --Qp_y {Qp_y:}" +
                      f" --id_state {id_state:}" +
                      f" --include_Zlong {include_Zlong:}" +
                      f" --harmonic_cavity {harmonic_cavity:}" +
                      f" --max_kick {max_kick}" + f" --sc {sc:}" + f" --ibs {ibs:}" +"\n")
    return command_string


def write_submission_script(sub_mode,
                            job_name,
                            job_time,
                            n_macroparticles=int(1e6),
                            n_turns=int(5e4),
                            n_bin=100,
                            bunch_current=1e-3,
                            Qp_x=1.6,
                            Qp_y=1.6,
                            id_state="open",
                            include_Zlong="False",
                            harmonic_cavity="False",
                            max_kick=1.6e-6,
                            sc='False',
                            ibs='False'):
    image_name = "soleil-pa:mbtrack2"
    script_name = "/home/dockeruser/transverse_instabilities/src/simulation/track_TI.py"
    command_string = get_command_string(script_name, n_macroparticles, n_turns,
                                        n_bin, bunch_current, Qp_x, Qp_y,
                                        id_state, include_Zlong,
                                        harmonic_cavity, max_kick, sc, ibs)
    src_folder = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/src/"
    data_folder = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities/data/"
    machine_data_folder = "/ccc/work/cont003/soleil/gubaiduv/facilities_mbtrack2/"
    with open(job_name, "w") as f:
        f.write("#!/bin/bash\n")
        if sub_mode == "ccrt":
            f.write("#MSUB -m work,scratch\n")
            if int(job_time) >= 86400:
                f.write("#MSUB -Q long\n")
            elif int(job_time) <= 1800:
                f.write("#MSUB -Q test\n")
            else:
                f.write("#MSUB -Q normal\n")
            f.write("#MSUB -q milan\n")
            f.write("#MSUB -n 1\n")
            f.write("#MSUB -c 8\n")
            f.write("#MSUB -T {:}\n".format(job_time))
            f.write("#MSUB -A soleil\n")
            # f.write("#MSUB -@ gubaidulinvadim@gmail.com:begin,end,requeue\n")
            f.write(
                f"#MSUB -o /ccc/cont003/home/soleil/gubaiduv/{job_name:}.err\n"
            )
            f.write(
                f"#MSUB -e /ccc/cont003/home/soleil/gubaiduv/{job_name:}.out\n"
            )
            f.write(f"module purge\n")
            f.write(f"module load mpi/openmpi/4.1.4\n")
            f.write(
                f"ccc_mprun -C {image_name:} -E'--ctr-module openmpi-4.1.4' -E'--ctr-mount src={src_folder:},dst=/home/dockeruser/transverse_instabilities/src/:src={machine_data_folder},dst=/home/dockeruser/facilities_mbtrack2/:src={data_folder},dst=/home/dockeruser/transverse_instabilities/data/' -- "
                + command_string)
        elif sub_mode == "slurm":
            f.write("#SBATCH --partition sumo\n")
            if is_longqueue == "True":
                f.write("#SBATCH -qos long\n")
            else:
                pass
            f.write("#SBATCH -n 8\n")
            f.write("#SBATCH --time={:}\n".format(job_time))
            f.write("#SBATCH --export=ALL\n")
            f.write("#SBATCH --mail-user='gubaidulinvadim@gmail.com'\n")
            f.write("#SBATCH --mail-type=begin,end,requeue\n")
            f.write(
                "#SBATCH --error=/home/sources/physmach/gubaidulin/err/{0:}_%I.err\n"
                .format(job_name))
            f.write("module load tools/singularity/current\n")
            f.write(
                f"singularity exec --no-home --B {mount_folder:} {image_name:}"
                + command_string)
        else:
            pass
    return job_name


if __name__ == "__main__":
    sys.path.append('/home/dockeruser/facilities_mbtrack2/')
    parser = get_parser_for_single_bunch()
    parser.add_argument(
        "--job_name",
        action="store",
        metavar="JOB_NAME",
        type=str,
        default="job",
        help=
        'Name of the job and associated .our and .err files. Defaults to "job"',
    )
    parser.add_argument(
        "--job_time",
        action="store",
        metavar="TIMELIMIT",
        type=str,
        default="100000",
        help=
        'Timelimit as a str for jobs on ccrt or slurm. Defaults to "100000"',
    )
    parser.add_argument(
        "--sub_mode",
        action="store",
        metavar="SUB_MODE",
        type=str,
        default="ccrt",
        help=
        'Submission mode. Accepted values are ["local", "ccrt", "slurm"], defaults to "ccrt"',
    )
    args = parser.parse_args()
    job = write_submission_script(args.sub_mode,
                                  args.job_name, args.job_time,
                                  args.n_macroparticles, args.n_turns,
                                  args.n_bin, args.bunch_current, args.Qp_x,
                                  args.Qp_y, args.id_state, args.include_Zlong,
                                  args.harmonic_cavity, args.max_kick, args.sc, args.ibs)
    print(args)
    if args.sub_mode == "ccrt":
        os.system("ccc_msub {:}".format(job))
    elif args.sub_mode == "slurm":
        os.system("sbatch {:}".format(job))
    else:
        pass
    os.system("rm -r {:}".format(job))
