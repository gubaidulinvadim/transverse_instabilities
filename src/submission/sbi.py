import os
from itertools import product
import numpy as np


def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, 
                       sc):
    return (
        f"python3 {script_name} --sub_mode ccrt"
        f" --job_name esrf_tmci_{bunch_current:.1e}_sc={sc}"
        f" --job_time 85000"
        f" --n_macroparticles {n_macroparticles}"
        f" --n_turns {n_turns}"
        f" --n_bin {n_bin}"
        f" --bunch_current {bunch_current}"
        f" --Qp_x {Qp_x}"
        f" --Qp_y {Qp_y}"
        f" --sc {sc}"
    )

def main():
    bunch_current = 1e-3 * np.linspace(0.2, 10, 50)
    sc = ['True', 'False']
    Qp = [4.0]
    combinations = product(bunch_current, sc, Qp)
    for (Ib, sc, Qp) in combinations:
        s = get_command_string(script_name='submission.py',
            n_macroparticles=500_000,
            n_turns=(50_000 if Qp==0 else 100_000),
            n_bin=100,
            bunch_current=Ib,
            Qp_x=Qp,
            Qp_y=Qp,
            sc=sc
            )
        try:
            os.system(s)
        except Exception as e:
            print(e)
            print(s)

if __name__ == "__main__":
    main()
