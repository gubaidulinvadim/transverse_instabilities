import os
from itertools import product
import numpy as np


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, max_kick, sc, ibs, quad):
    return (
        f"python3 {script_name} --sub_mode ccrt"
        f" --job_name tmci_{bunch_current:.1e}_sc={sc}_hc={harmonic_cavity}_Z={include_Zlong}_ibs={ibs}"
        f" --job_time 85000"
        f" --n_macroparticles {n_macroparticles}"
        f" --n_turns {n_turns}"
        f" --n_bin {n_bin}"
        f" --bunch_current {bunch_current}"
        f" --Qp_x {Qp_x}"
        f" --Qp_y {Qp_y}"
        f" --id_state {id_state}"
        f" --include_Zlong {include_Zlong}"
        f" --harmonic_cavity {harmonic_cavity}"
        f" --max_kick {max_kick}"
        f" --sc {sc}"
        f" --ibs {ibs}"
        f" --quad {quad}"
    )

def main():
    bunch_current = 1e-3 * np.linspace(0.2, 12, 60)
    id_state = 'close'
    Zlong = ['True']
    hc = ['False', 'True']
    sc = ['True']
    ibs= ['True']
    Qp = [1.6]
    quad = ['True']
    combinations = product(bunch_current, Zlong, hc, sc, Qp, ibs)
    for (Ib, Zlong, hc, sc, Qp, ibs) in combinations:
        s = get_command_string(script_name='submission.py',
            n_macroparticles=500_000,
            n_turns=(50_000 if Qp==0 else 75_000),
            n_bin=100,
            bunch_current=Ib,
            Qp_x=Qp,
            Qp_y=Qp,
            id_state=id_state,
            include_Zlong=Zlong,
            harmonic_cavity=hc,
            max_kick=0,
            sc=sc,
            ibs=ibs,
            quad=quad)
        try:
            os.system(s)
        except Exception as e:
            print(e)
            print(s)

if __name__ == "__main__":
    main()
