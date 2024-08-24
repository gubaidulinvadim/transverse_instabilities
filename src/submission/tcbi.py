import os
from itertools import product
import numpy as np

def get_command_string(script_name, n_macroparticles, n_turns, n_bin,
                       bunch_current, Qp_x, Qp_y, id_state, include_Zlong,
                       harmonic_cavity, max_kick, n_turns_wake, sc, ibs):
    return (
        f"python {script_name} --sub_mode ccrt"
        f" --job_name TBCIchroma{Qp_y:.1f}_current_{bunch_current:.1e}_sc_{sc}"
        f" --job_time 86000"
        f" --n_macroparticles {n_macroparticles}"
        f" --n_turns {n_turns}"
        f" --n_bin {n_bin}"
        f" --bunch_current {bunch_current}"
        f" --Qp_x {Qp_x}"
        f" --Qp_y {Qp_y}"
        f" --id_state {id_state}"
        f" --include_Zlong {include_Zlong}"
        f" --harmonic_cavity {harmonic_cavity}"
        f" --n_turns_wake {n_turns_wake}"
        f" --max_kick {max_kick}"
        f" --sc {sc}"
        f" --ibs {ibs}"
    )

def run_simulation(script_name, n_macroparticles, n_turns, n_bin, chromaticity_list, bunch_current_list, id_state, zlong_hc_pairs, sc_list, n_turns_wake, ibs_list, max_kick=0):
    for chromaticity in chromaticity_list:
        for bunch_current in bunch_current_list:
            combinations = product(zlong_hc_pairs, sc_list, ibs_list)
            for (include_Zlong, harmonic_cavity), sc, ibs in combinations:
                command = get_command_string(
                    script_name=script_name,
                    n_macroparticles=n_macroparticles,
                    n_turns=n_turns,
                    n_bin=n_bin,
                    bunch_current=bunch_current,
                    Qp_x=chromaticity,
                    Qp_y=chromaticity,
                    id_state=id_state,
                    include_Zlong=include_Zlong,
                    harmonic_cavity=harmonic_cavity,
                    max_kick=max_kick,
                    n_turns_wake=n_turns_wake,
                    sc=sc,
                    ibs=ibs
                )
                try:
                    os.system(command)
                except Exception as e:
                    print(f"Error executing command: {command}")
                    print(e)

def main():
    script_name = 'submission_mb.py'
    n_macroparticles = int(1e5)
    n_turns = 100_000
    n_bin = 100
    n_turns_wake = 50
    max_kick = 0
    id_state = 'close'
    
    chromaticity_list_1 = np.linspace(0.2, 3.0, 15)
    bunch_current_list_1 = [1.2e-3]
    
    # chromaticity_list_2 = [1.6]
    # bunch_current_list_2 = np.linspace(1.2e-3, 3.6e-3, 13)

    zlong_hc_pairs = [('True', 'False')]
    sc_list = ['True']
    ibs_list = ['True']
    run_simulation(
        script_name=script_name,
        n_macroparticles=n_macroparticles,
        n_turns=n_turns,
        n_bin=n_bin,
        chromaticity_list=chromaticity_list_1,
        bunch_current_list=bunch_current_list_1,
        id_state=id_state,
        zlong_hc_pairs=zlong_hc_pairs,
        sc_list=sc_list,
        n_turns_wake=n_turns_wake,
        max_kick=max_kick,
        ibs_list=ibs_list
    )
    
    # run_simulation(
    #     script_name=script_name,
    #     n_macroparticles=n_macroparticles,
    #     n_turns=n_turns,
    #     n_bin=n_bin,
    #     chromaticity_list=chromaticity_list_2,
    #     bunch_current_list=bunch_current_list_2,
    #     id_state=id_state,
    #     zlong_hc_pairs=zlong_hc_pairs,
    #     sc_list=sc_list,
    #     n_turns_wake=n_turns_wake,
    #     max_kick=max_kick
    # )

if __name__ == "__main__":
    main()
