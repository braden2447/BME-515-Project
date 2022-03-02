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

# load run controls
h.load_file('stdrun.hoc')

# set temp
h.celsius = 37

# MODEL SPECIFICATION
# time params =========================================================================
h.tstop =  4 # [ms]: simulation time
h.dt = 0.001 # [ms]: timestep

# cell params =========================================================================
Vo = -80 # [mV]: Vm @ rest for initializing membrane potential at start of simulation
n_nodes = 51 # []: (int) number of sections, make this an odd number
D = 12 # [um]: fiber diameter
inl = 100*D # [um]: internodal length
rhoa = 54.7 # [Ohm]: axoplasmic/axial resistivity
cm = 2.5 # [uF/cm**2]
L = 1.5 # [um]
nseg = 1 # []: (int)
g = 1/2000 # [S/cm**2] 

# material params =====================================================================
sigma_e = 2e-4 # [S/mm]: extracellular medium resistivity

# stim params =========================================================================
delay = 1 # [ms]: start time of stim
dur = .2# [ms]: pulse width of (monopolar) stim
amp = 0.6 # [nA]: amplitude of (intracellular) stim object -- but we are applying this extracellular (negative cathodic, positive anodic)
e2f = 1   # [mm]: electrode to fiber distance

# MODEL INITIALIZATION
# define nodes for cell =================================================================
nodes = [h.Section(name=f'node[{i}]') for i in range(n_nodes)]
# f-string (as shown) is my personal preference, but also 
#   ='node[{}]'.format(i) OR 
#   ='node[%d]' % i

# insert extracellular/mechanisms part of the circuit ===================================
# connect the nodes =====================================================================
for node_ind, node in enumerate(nodes):
    node.nseg = nseg
    node.diam = 0.6*D
    node.L = L
    node.Ra = rhoa*((L+inl)/L) # left this in here since it is a fn(*other params)
    node.cm = cm

    node.insert('AXNODE')
    node.insert('extracellular')

    for seg in node:
        #seg.pas.g = g
        seg.extracellular.e = 0
    if node_ind>0:
        node.connect(nodes[node_ind-1](1))

# INSTRUMENTATION - STIMULATION/RECORDING
# make dummy object to "host" the stim - this will make sense later ===================
dummy = h.Section(name='dummy')
e_stim_obj = h.IClamp(dummy(0.5)) # puts the stim halfway along the length

e_stim_obj.dur = dur
e_stim_obj.amp = amp
e_stim_obj.delay = delay



# create neuron "vector" for recording membrane potentials =================================
vol_mem = [h.Vector().record(sec(0.5)._ref_v) for sec in nodes]
tvec = h.Vector().record(h._ref_t)

# SIMULATION CONTROL
# compute extracellular potentials from point current source (call this from my_advance to update at each timestep)
def update_field():
    #print(h.t)
    phi_e = []
    ### Use for biphasic stim

    #if h.t <= (delay + dur/2):
        #e_stim_obj.amp = amp
    #else:
        #e_stim_obj.amp = -1*amp
        
    for node_ind, node in enumerate(nodes):
        x_loc = 1e-3*(-(n_nodes-1)/2*inl + inl*node_ind) # 1e-3 [um] -> [mm]
        r = np.sqrt(x_loc**2 + e2f**2) # [mm]

        # ========== left these in so you can check out in debugger ==========
        # x_axon.append(x_loc) # centered at middle node for an odd # of nodes
        # r.append(np.sqrt(x_loc**2 + e2f**2)) # [mm]
        phi_e.append(e_stim_obj.i/(4*sigma_e*np.pi*r))
        node(0.5).e_extracellular = phi_e[node_ind]

# time integrate with constant time step - this just defines method, called by proc advance() below
def my_advance():
    update_field()
    h.fadvance()

h.finitialize(Vo)

# this is somewhat of a "hack" to change the default run procedure in HOC ==================
h(r"""
proc advance() {
    nrnpython("my_advance()")
}""")

# run until tstop ==========================================================================
h.continuerun(h.tstop)

# DATA POST PROCESSING / OUTPUT
# plot things ==============================================================================
print(vol_mem)
plt.plot(tvec, vol_mem[50])
plt.xlabel('time (ms)')
plt.ylabel('Vm (mA)')
plt.show()

print('============ DONE ============')

#plotting different nodes overlayed
plt.figure()
my_nodes = vol_mem[20:30]
                
for node in my_nodes:
    plt.plot(tvec, node)
plt.xlabel('Time (ms)')
plt.ylabel('Vm (mA)')
plt.title('Anodic Activation sites for nodes 21-30 (dur = 200 us)')
plt.legend([21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
plt.xlim(0.975,1.3)
plt.ylim((-155, 0))
plt.show()


