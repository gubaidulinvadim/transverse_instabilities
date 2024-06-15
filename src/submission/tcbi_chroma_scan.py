import os

import numpy as np


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, max_kick, n_turns_wake):
    command_string = (
        f"python {script_name:}" + f" --sub_mode ccrt" +
        f" --is_longqueue True" +
        f" --job_name TBCIchroma{Qp_y:.1f}_current_{bunch_current:.1e}" +
        f" --job_time 8000" + f" --n_macroparticles {n_macroparticles:}" +
        f" --n_turns {n_turns:}" + f" --n_bin {n_bin:}" +
        f" --bunch_current {bunch_current:}" + f" --Qp_x {Qp_x:}" +
        f" --Qp_y {Qp_y:}" + f" --id_state {id_state:}" +
        f" --include_Zlong {include_Zlong:}" +
        f" --harmonic_cavity {harmonic_cavity:}" +
        f" --n_turns_wake {n_turns_wake}" + f" --max_kick {max_kick}" + "\n")
    return command_string


chromaticity = [.5]  #, 1.0, 1.5, 2.0, 2.5, 3.0] #26
id_state = 'close'
for zlong, hc in [('True', 'False')]:
    # for zlong, hc in [('True', 'False'), ('False', 'False'), ('True', 'True')]:
    for Qp in chromaticity:
        s = get_command_string(script_name='submission_mb.py',
                               n_macroparticles=int(1e4),
                               n_turns=10_000,
                               n_bin=100,
                               bunch_current=1.2e-3,
                               Qp_x=Qp,
                               Qp_y=Qp,
                               id_state=id_state,
                               include_Zlong=zlong,
                               harmonic_cavity=hc,
                               max_kick=0,
                               n_turns_wake=50)
        os.system(s)
