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
fiber = MRG(5.7, 51) # D = 5.7, 7.3, 8.7, 10, 11.5, 12.8, 14, 15, 16

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
amp = -26.3 # [mA (EC)/nA (IC)]: amplitude of stim object -- but we are applying this extracellular:(-)cathodic, (+)anodic)
# e2f = 7.53 # [mm]: electrode to fiber distance (4.27 mm - STNm, 7.53 STNl))
x_e2f = 19.26 # [mm]: x distance of closest electrode to first node - SON=19.26, STN=10.6
y_e2f = 15 # [mm]: y distance of closest electrode to first node - SON=15, STN=6.3
z_e2f = 3 # [mm]: depth of fiber to surface of skin (electrode on surface) - SON=3, STN=3

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
        y_loc = y_e2f + 1e-3*(fiber.deltax * node_ind) # 1e-3 [um] -> [mm]
        r1 = np.sqrt(x_e2f**2 + y_loc**2 + z_e2f**2)
        r2 = np.sqrt((x_e2f+13)**2 + y_loc**2 + z_e2f**2) # 13 mm electrode separation
        phi_e.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        node(0.5).e_extracellular = phi_e[node_ind]

    for mysa_ind, mysa in enumerate(fiber.MYSA):
        if mysa_ind%2 == 0: # Even MYSA index case - first MYSA of section
            y_loc = y_e2f + 1e-3*(fiber.deltax * (mysa_ind/2) + 1.5) # 1.5 um separation from end of node to center of MYSA
        else:
            y_loc = y_e2f + 1e-3*(fiber.deltax * np.trunc(mysa_ind/2) + 1.5 * fiber.paralength1 + 2 * fiber.paralength2 +
                                  6 * fiber.interlength)
        r1 = np.sqrt(x_e2f**2 + y_loc**2 + z_e2f**2)
        r2 = np.sqrt((x_e2f+13)**2 + y_loc**2 + z_e2f**2)
        mysa_phi.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        mysa(0.5).e_extracellular = mysa_phi[mysa_ind]

    for flut_ind, flut in enumerate(fiber.FLUT):
        if flut_ind%2 == 0: # Even FLUT index case - first FLUT of section
            y_loc = y_e2f + 1e-3*(fiber.deltax * (flut_ind/2) + 3 + fiber.interlength/2)
        else:
            y_loc = y_e2f + 1e-3*(fiber.deltax * np.trunc(flut_ind/2) + fiber.paralength1 + 1.5 * fiber.paralength2 +
                                  6 * fiber.interlength)
        r1 = np.sqrt(x_e2f**2 + y_loc**2 + z_e2f**2)
        r2 = np.sqrt((x_e2f+13)**2 + y_loc**2 + z_e2f**2)
        flut_phi.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        flut(0.5).e_extracellular = flut_phi[flut_ind]

    for stin_ind, stin in enumerate(fiber.STIN):
        if stin_ind%6 == 0:
            stin_count = 0
        else:
            stin_count = 6 - stin_ind%6
        y_loc = y_e2f + 1e-3*(fiber.deltax * np.trunc(stin_ind/6) + fiber.paralength1 + fiber.paralength2 +
                              (stin_count + 0.5) * fiber.interlength)
        r1 = np.sqrt(x_e2f**2 + y_loc**2 + z_e2f**2)
        r2 = np.sqrt((x_e2f+13)**2 + y_loc**2 + z_e2f**2)
        stin_phi.append((e_stim_obj.i / (4 * sigma_e * np.pi * r1)) + (-1 * e_stim_obj.i / (4 * sigma_e * np.pi * r2)))
        stin(0.5).e_extracellular = stin_phi[stin_ind]


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
# AP POST PROCESSING
print(max(vol_mem[50]))
if max(vol_mem[50]) > 0:
    print("Axon activated.")
else:
    print("Axon NOT activated.")

# plot things ==============================================================================
# print(vol_mem)
plt.plot(tvec, vol_mem[50])
plt.xlabel('Time (ms)')
plt.ylabel('Vm (mV)')
plt.title('Membrane Potential vs Time: D = 16 um, Amp = 11.5 mA')
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
