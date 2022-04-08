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
h.tstop = 5 # [ms]: simulation time
h.dt = 0.001 # [ms]: timestep

# cell parameters defined in MRG model

# material params =====================================================================
sigma_e = 0.00043 # [S/mm]: extracellular medium resistivity (skin)

# stim params =========================================================================
delay = 1 # [ms]: start time of stim
dur = 0.25 # [ms]: pulse width of (monopolar) stim
amp = 11.4 # [mA (EC)/nA (IC)]: amplitude of stim object -- but we are applying this extracellular (negative cathodic, positive anodic)
e2f = 7.53 # [mm]: electrode to fiber distance (4.27 mm - STNm, 7.53 STNl))

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
    mysa_phi = []
    flut_phi = []
    stin_phi = []
        
    for node_ind, node in enumerate(fiber.node):
        # Bipolar stimulus
        x_loc1 = 1e-3 * (-(fiber.axonnodes - 1) / 2 * fiber.deltax + fiber.deltax * node_ind)  # 1e-3 [um] -> [mm]
        x_loc2 = x_loc1 + 13  # Shifted 13 mm from first contact
        r1 = np.sqrt(x_loc1 ** 2 + e2f ** 2)  # [mm]
        r2 = np.sqrt(x_loc2 ** 2 + e2f ** 2)  # [mm]
        phi_e.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        node(0.5).e_extracellular = phi_e[node_ind]

'''
    for mysa_ind, mysa in enumerate(fiber.MYSA):
        # x_loc1 = 1e-3 * (-(fiber.paranodes1 - 1) / 2 * fiber.)
        # x_loc2 = x_loc1 + 13
        # mysa(0.5).e_extracellular = mysa_phi[mysa_ind]

    for flut_ind, flut in enumerate(fiber.FLUT):
        # flut(0.5).e_extracellular = flut_phi[flut_ind]

    for stin_ind, stin in enumerate(fiber.STIN):
        # stin(0.5)._extracellular = stin_phi[stin_ind]
'''

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
plt.plot(tvec, vol_mem[0])
plt.xlabel('Time (ms)')
plt.ylabel('Vm (mV)')
plt.title('Membrane Potential vs Time: D = 5.7 um, Amp = 11.5 mA')
plt.show()


# Stimulation Waveform Plot
# current = [0]*200
# current50 = [0]*50
# l6 = [16]*250
# l6minus = [-16]*250
# currentF = current+l6+l6minus+current+current50+current50
# time = list(range(1000))
# plt.plot(time, currentF)
# plt.xlabel('Time (us)')
# plt.ylabel('Current Stimulus (mA)')
# plt.title('Stimulation Waveform: Amp = 16 mA, Dur = 250 us')
# plt.show()'''

print('============ DONE ============')
