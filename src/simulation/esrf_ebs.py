# -*- coding: utf-8 -*-
"""
ESRF-EBS parameters script.
Only longitudinal paramters are correct.

@author: Vadim Gubaidulin 
"""

import numpy as np
from mbtrack2.tracking import Synchrotron, Electron
from mbtrack2.utilities import Optics 

def esrf_ebs():
    
    h = 992
    L = 843.977
    E0 = 6e9
    particle = Electron()
    ac = 8.511729e-05
    U0 = 2.532506e+06
    tau = np.array([0.00870384, 0.01333954, 0.00909062])
    tune = np.array([76.21, 27.34])
    emit = np.array([110e-12, 5e-12])
    sigma_0 = 9.744e-12
    sigma_delta = 9.356e-4
    chro = [0, 0]
    
    # mean values
    beta = np.array([4.16, 7.66])
    alpha = np.array([0, 0])
    dispersion = np.array([0, 0, 0, 0])
    optics = Optics(local_beta=beta, local_alpha=alpha, 
                      local_dispersion=dispersion)
    
    ring = Synchrotron(h, optics, particle, L=L, E0=E0, ac=ac, U0=U0, tau=tau,
                       emit=emit, tune=tune, sigma_delta=sigma_delta, 
                       sigma_0=sigma_0, chro=chro)
    
    return ring
