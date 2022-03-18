#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 13:00:54 2022

@author: shanebeyer
"""

# import NEURON library
from neuron import h
import matplotlib.pyplot as plt

# other imports
import numpy as np
from mrg import MRG

# load run controls
h.load_file('stdrun.hoc')

# set temp
h.celsius = 37

# create MRG fiber model
fiber = MRG(5.7, 51)

# MODEL SPECIFICATION
# time params =========================================================================
h.tstop = 25 # [ms]: simulation time
h.dt = 0.001 # [ms]: timestep

# cell parameters defined in MRG model

# material params =====================================================================
sigma_e = 0.00043 # [S/mm]: extracellular medium resistivity (skin)

# stim params =========================================================================
delay = 1 # [ms]: start time of stim
dur = 0.25 # [ms]: pulse width of (monopolar) stim
amp = 5 # [mA (EC)/nA (IC)]: amplitude of stim object -- but we are applying this extracellular (negative cathodic, positive anodic)
e2f = 3 # [mm]: electrode to fiber distance

# MODEL INITIALIZATION
# define nodes for cell =================================================================
# defined in MRG model
# nodes = [h.Section(name=f'node[{i}]') for i in range(n_nodes)]

# insert extracellular/mechanisms part of the circuit ===================================
# Handled by MRG model

# INSTRUMENTATION - STIMULATION/RECORDING
# make dummy object to "host" the stim - this will make sense later ===================
dummy = h.Section(name='dummy')
e_stim_obj = h.IClamp(dummy(0.5)) # puts the stim halfway along the length

e_stim_obj.dur = dur
e_stim_obj.amp = amp
e_stim_obj.delay = delay


# create neuron "vector" for recording membrane potentials =================================
vol_mem = [h.Vector().record(sec(0.5)._ref_v) for sec in fiber.node]
tvec = h.Vector().record(h._ref_t)

# SIMULATION CONTROL
# compute extracellular potentials from point current source (call this from my_advance to update at each timestep)
def update_field():
    #print(h.t)
    phi_e = []
        
    for node_ind, node in enumerate(fiber.node):
        # Bipolar stimulus
        x_loc1 = 1e-3 * (-(fiber.axonnodes - 1) / 2 * fiber.interlength + fiber.interlength * node_ind)  # 1e-3 [um] -> [mm]
        x_loc2 = x_loc1 + 13  # Shifted 13 mm from first contact
        r1 = np.sqrt(x_loc1 ** 2 + e2f ** 2)  # [mm]
        r2 = np.sqrt(x_loc2 ** 2 + e2f ** 2)  # [mm]
        phi_e.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        node(0.5).e_extracellular = phi_e[node_ind]

        # ========== left these in so you can check out in debugger ==========
        # x_axon.append(x_loc) # centered at middle node for an odd # of nodes
        # r.append(np.sqrt(x_loc**2 + e2f**2)) # [mm]

# time integrate with constant time step - this just defines method, called by proc advance() below
def my_advance():
    update_field()
    h.fadvance()

h.finitialize(fiber.v_init)

# this is somewhat of a "hack" to change the default run procedure in HOC ==================
h(r"""
proc advance() {
    nrnpython("my_advance()")
}""")

# run until tstop ==========================================================================
h.continuerun(h.tstop)

# DATA POST PROCESSING / OUTPUT
# plot things ==============================================================================
# print(vol_mem)
plt.plot(tvec, vol_mem[25])
plt.xlabel('Time (ms)')
plt.ylabel('Vm (mA)')
plt.show()

print('============ DONE ============')
