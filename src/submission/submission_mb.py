import argparse
import os

from utils import get_parser_for_single_bunch, get_parser_for_multibunch


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, n_turns_wake, max_kick, sc):
    """
    Generate the command string to execute the simulation script with given parameters.
    """
    return (
        f"python -u {script_name} "
        f"--n_macroparticles {n_macroparticles} "
        f"--n_turns {n_turns} "
        f"--n_bin {n_bin} "
        f"--bunch_current {bunch_current} "
        f"--Qp_x {Qp_x} "
        f"--Qp_y {Qp_y} "
        f"--id_state {id_state} "
        f"--include_Zlong {include_Zlong} "
        f"--harmonic_cavity {harmonic_cavity} "
        f"--n_turns_wake {n_turns_wake} "
        f"--max_kick {max_kick} "
        f"--sc {sc}\n"
    )


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
                            n_tasks=4,
                            n_turns_wake=50,
                            max_kick=1.6e-6,
                            sc="False"):
    script_name = "/home/dockeruser/transverse_instabilities/src/simulation/track_mb.py"
    image_name = "soleil-pa:mbtrack2-develop"
    mount_folder = "/ccc/work/cont003/soleil/gubaiduv/transverse_instabilities"
    machine_data_folder = "/ccc/work/cont003/soleil/gubaiduv/machine_data"
    
    command_string = get_command_string(script_name, n_macroparticles, n_turns,
                                        n_bin, bunch_current, Qp_x, Qp_y,
                                        id_state, include_Zlong,
                                        harmonic_cavity, n_turns_wake,
                                        max_kick, sc)
    submission_script_path = f"{job_name}.sh"
    
    with open(submission_script_path, "w") as f:
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
            f.write(f"#MSUB -n {n_tasks}\n")
            f.write(f"#MSUB -c 1\n")
            f.write(f"#MSUB -T {job_time}\n")
            f.write("#MSUB -A soleil\n")
            f.write("#MSUB -@ gubaidulinvadim@gmail.com:begin,end,requeue\n")
            f.write(f"#MSUB -o /ccc/cont003/home/soleil/gubaiduv/{job_name}.err\n")
            f.write(f"#MSUB -e /ccc/cont003/home/soleil/gubaiduv/{job_name}.out\n")
            f.write("module purge\n")
            f.write("module load mpi/openmpi/4.1.4\n")
            f.write(
                f"ccc_mprun -C {image_name} "
                f"-E'--ctr-module openmpi-4.1.4' "
                f"-E'--ctr-mount src={mount_folder},dst=/home/dockeruser/transverse_instabilities:src={machine_data_folder},dst=/home/dockeruser/machine_data' "
                f"-- {command_string}"
            )
        elif sub_mode == "slurm":
            f.write("#SBATCH --partition sumo\n")
            if is_longqueue == "True":
                f.write("#SBATCH --qos long\n")
            f.write("#SBATCH -n 8\n")
            f.write(f"#SBATCH --time={job_time}\n")
            f.write("#SBATCH --export=ALL\n")
            f.write("#SBATCH --mail-user=gubaidulinvadim@gmail.com\n")
            f.write("#SBATCH --mail-type=begin,end,requeue\n")
            f.write(f"#SBATCH --error=/home/sources/physmach/gubaidulin/err/{job_name}_%I.err\n")
            f.write("module load tools/singularity/current\n")
            f.write(
                f"singularity exec --no-home --B {mount_folder} {image_name} "
                f"{command_string}"
            )
        else:
            raise ValueError("Unsupported submission mode")

    return submission_script_path

if __name__ == "__main__":
    os.environ['KMP_DUPLICATE_LIB_OK']='True'
    parser = get_parser_for_multibunch()
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
    parser.add_argument(
        "--n_tasks",
        action="store",
        metavar="N_TASKS",
        type=int,
        default=4,
        help=
        "Number of tasks assigned for mpi, should be larger than number of bunches. Defaults to 500.",
    )
    args = parser.parse_args()
    job = write_submission_script(
        args.sub_mode, args.job_name, args.job_time,
        args.n_macroparticles, args.n_turns, args.n_bin, args.bunch_current,
        args.Qp_x, args.Qp_y, args.id_state, args.include_Zlong,
        args.harmonic_cavity, args.n_tasks, args.n_turns_wake, args.max_kick, args.sc)
    print(args)
    if args.sub_mode == "ccrt":
        os.system("ccc_msub {:}".format(job))
    elif args.sub_mode == "slurm":
        os.system("sbatch {:}".format(job))
    else:
        pass
    os.system("rm -r {:}".format(job))
