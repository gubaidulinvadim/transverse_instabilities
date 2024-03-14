import os
import numpy as np
def get_command_string(
    script_name,
    n_macroparticles,
    n_turns,
    n_bin,
    bunch_current,
    Qp_x,
    Qp_y,
    id_state,
    include_Zlong,
    harmonic_cavity,
    max_kick
):
    command_string = (
        f"python {script_name:}"
        + f" --n_macroparticles {n_macroparticles:}"
        + f" --n_turns {n_turns:}"
        + f" --n_bin {n_bin:}"
        + f" --bunch_current {bunch_current:}"
        + f" --Qp_x {Qp_x:}"
        + f" --Qp_y {Qp_y:}"
        + f" --id_state {id_state:}"
        + f" --include_Zlong {include_Zlong:}"
        + f" --harmonic_cavity {harmonic_cavity:}"
        + f" --max_kick {max_kick}" 
        + "\n"
    )
    return command_string

bunch_current  = np.linspace(0, 7, 36)
print(bunch_current)
for Ib in bunch_current:
    s = command_string(script_name = 'src/submission/submission.py',
    n_macropaticles=int(1e6),
    n_turns=int(5e4),
    n_bin=100,
    bunch_current=Ib,
    Qp_x=0.0,
    Qp_y=0.0,
    id_state=id_state,
    include_Zlong="False",
    harmonic_cavity="False",
    max_kick=0)

    os.system(s)