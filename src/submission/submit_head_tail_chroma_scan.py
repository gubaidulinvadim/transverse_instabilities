import os

import numpy as np


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, max_kick, sc):
    command_string = (
        f"python {script_name:}" + f" --sub_mode ccrt"
        # + f" --is_longqueue True"
        + f" --job_name HTchroma{Qp_y:.1f}_current_{bunch_current:.1e}" +
        f" --job_time 86000" + f" --n_macroparticles {n_macroparticles:}" +
        f" --n_turns {n_turns:}" + f" --n_bin {n_bin:}" +
        f" --bunch_current {bunch_current:}" + f" --Qp_x {Qp_x:}" +
        f" --Qp_y {Qp_y:}" + f" --id_state {id_state:}" +
        f" --include_Zlong {include_Zlong:}" +
        f" --harmonic_cavity {harmonic_cavity:}" + f" --max_kick {max_kick}" +
        f" --sc {sc}" + "\n")
    return command_string


chromaticity = np.linspace(0, 5, 51)
id_state = 'close'
for Ib in [1.2e-3, 6.25e-3]:
    for Qp in chromaticity:
        # for Zlong, hc in [('False', 'False'), ('True', 'False'), ('True', 'True')]:
        for Zlong, hc in [('False', 'False')]:
            s = get_command_string(script_name='submission.py',
                                   n_macroparticles=int(1e6),
                                   n_turns=100_000,
                                   n_bin=100,
                                   bunch_current=Ib,
                                   Qp_x=Qp,
                                   Qp_y=Qp,
                                   id_state=id_state,
                                   include_Zlong=Zlong,
                                   harmonic_cavity=hc,
                                   max_kick=0.0e+00,
                                   sc='False')
            os.system(s)
