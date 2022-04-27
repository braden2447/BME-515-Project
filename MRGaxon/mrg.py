"""
A port of the MRG fiber model to python.
Hasn't been tested for bugs.

All the parameters defined in the original hoc
script should be accessible as instance variables.

@Author: Minhaj Hussain (minhaj.hussain@duke.edu)
@Date: 2022-02-24

@copyright: Copyright (c) 2022

Originally:
2/02
Cameron C. McIntyre
SIMULATION OF PNS MYELINATED AXON

This model is described in detail in:

McIntyre CC, Richardson AG, and Grill WM. Modeling the excitability of
mammalian nerve fibers: influence of afterpotentials on the recovery
cycle. Journal of Neurophysiology 87:995-1006, 2002.
"""

import math
from neuron import h


class MRG:

    def __init__(self, diameter, nodes):
        # check the diameter is one used in the original MRG implementation
        if diameter not in {1, 2, 3, 4, 5, 5.7, 7.3, 8.7, 10.0, 11.5, 12.8, 14.0, 15.0, 16.0}:
            raise ValueError(f'{diameter} is not one of the original MRG fiber diameters')
        gp = self.geometric_params(diameter)

        self.axonD = gp['axonD']
        self.nodeD = gp['nodeD']
        self.paraD1 = gp['paraD1']
        self.paraD2 = gp['paraD2']
        self.deltax = gp['deltax']
        self.paralength2 = gp['paralength2']
        self.nl = gp['nl']
        self.rhoa = gp['rhoa']
        self.nodelength = gp['nodelength']
        self.paralength1 = gp['paralength1']
        self.space_p1 = gp['space_p1']
        self.space_p2 = gp['space_p2']
        self.space_i = gp['space_i']
        self.Rpn0 = gp['Rpn0']
        self.Rpn1 = gp['Rpn1']
        self.Rpn2 = gp['Rpn2']
        self.Rpx = gp['Rpx']
        self.interlength = gp['interlength']

        # initialize instance variables that will be set later
        self.axonnodes = nodes
        self.paranodes1 = None
        self.paranodes2 = None
        self.axoninter = None

        self.mycm = None
        self.mygm = None
        self.e_pas_Vrest = None

        self.v_init = -80
        self.diameter = diameter

        # -- compartment subsets --
        self.node = []
        self.MYSA = []
        self.FLUT = []
        self.STIN = []

        self.create_sections(nodes)
        self.build_topology(nodes)
        self.define_geometry()
        self.define_biophysics()

        self.all = h.SectionList()
        self.all.wholetree(sec=self.node[0])
        self.py_all = list(self.all)

        self.init_voltages()

    @staticmethod
    def geometric_params(diameter):
        """Generate geometric parameters for fiber model."""
        params = MRG._classic_geometric_params(diameter)
        params.update(MRG._complete_geometric_params(**params))
        return params

    @staticmethod
    def _classic_geometric_params(fiberD):
        # if fiberD == 1.0:
        #     axonD = 0.8
        #     nodeD = 0.7
        #     paraD1 = 0.7
        #     paraD2 = 0.8
        #     deltax = 100
        #     paralength2 = 5
        #     nl = 15
        # elif fiberD == 2.0:
        #     axonD = 1.6
        #     nodeD = 1.4
        #     paraD1 = 1.4
        #     paraD2 = 1.6
        #     deltax = 200
        #     paralength2 = 10
        #     nl = 30
        if fiberD == 1 or 2 or 3 or 4 or 5:
            nl = -0.4749 * fiberD**2 + 16.85 * fiberD - 0.7648
            nodeD = 0.01093 * fiberD**2 + 0.1008 * fiberD + 1.099
            paraD1 = nodeD
            paraD2 = 0.02361 * fiberD**2 + 0.3673 * fiberD + 0.7122
            axonD = paraD2
            paralength2 = -0.1652 * fiberD**2 + 6.354 * fiberD - 0.2862
            deltax = 81.08 * fiberD + 37.84
        elif fiberD == 5.7:
            axonD = 3.4
            nodeD = 1.9
            paraD1 = 1.9
            paraD2 = 3.4
            deltax = 500
            paralength2 = 35
            nl = 80
        elif fiberD == 7.3:
            axonD = 4.6
            nodeD = 2.4
            paraD1 = 2.4
            paraD2 = 4.6
            deltax = 750
            paralength2 = 38
            nl = 100
        elif fiberD == 8.7:
            axonD = 5.8
            nodeD = 2.8
            paraD1 = 2.8
            paraD2 = 5.8
            deltax = 1000
            paralength2 = 40
            nl = 110
        elif fiberD == 10.0:
            axonD = 6.9
            nodeD = 3.3
            paraD1 = 3.3
            paraD2 = 6.9
            deltax = 1150
            paralength2 = 46
            nl = 120
        elif fiberD == 11.5:
            axonD = 8.1
            nodeD = 3.7
            paraD1 = 3.7
            paraD2 = 8.1
            deltax = 1250
            paralength2 = 50
            nl = 130
        elif fiberD == 12.8:
            axonD = 9.2
            nodeD = 4.2
            paraD1 = 4.2
            paraD2 = 9.2
            deltax = 1350
            paralength2 = 54
            nl = 135
        elif fiberD == 14.0:
            axonD = 10.4
            nodeD = 4.7
            paraD1 = 4.7
            paraD2 = 10.4
            deltax = 1400
            paralength2 = 56
            nl = 140
        elif fiberD == 15.0:
            axonD = 11.5
            nodeD = 5.0
            paraD1 = 5.0
            paraD2 = 11.5
            deltax = 1450
            paralength2 = 58
            nl = 145
        elif fiberD == 16.0:
            axonD = 12.7
            nodeD = 5.5
            paraD1 = 5.5
            paraD2 = 12.7
            deltax = 1500
            paralength2 = 60
            nl = 150
        return {
            'axonD': axonD, 'nodeD': nodeD, 'paraD1': paraD1, 'paraD2': paraD2,
            'deltax': deltax, 'paralength2': paralength2, 'nl': nl
        }

    @staticmethod
    def _complete_geometric_params(nodeD, paraD1, paraD2, axonD, deltax,
                                   paralength2, nl):
        rhoa = 0.7e6        # [ohm-um] axoplasmic resistivity
        nodelength = 1.0    # Length of node of ranvier [um]
        paralength1 = 3     # Length of MYSA [um]
        space_p1 = 0.002    # Thickness of periaxonal space in MYSA [um]
        space_p2 = 0.004    # Thickness of periaxonal space in FLUT [um]
        space_i = 0.004     # Thickness of periaxonal space in STIN [um]
        Rpn0 = (rhoa * .01) / (math.pi * ((((nodeD / 2) + space_p1) ** 2) - ((nodeD / 2) ** 2)))
        Rpn1 = (rhoa * .01) / (math.pi * ((((paraD1 / 2) + space_p1) ** 2) - ((paraD1 / 2) ** 2)))
        Rpn2 = (rhoa * .01) / (math.pi * ((((paraD2 / 2) + space_p2) ** 2) - ((paraD2 / 2) ** 2)))
        Rpx = (rhoa * .01) / (math.pi * ((((axonD / 2) + space_i) ** 2) - ((axonD / 2) ** 2)))
        interlength = (deltax - nodelength - (2 * paralength1) - (2 * paralength2)) / 6
        return {
            'rhoa': rhoa, 'nodelength': nodelength, 'paralength1': paralength1,
            'space_p1': space_p1, 'space_p2': space_p2, 'space_i': space_i,
            'Rpn0': Rpn0, 'Rpn1': Rpn1, 'Rpn2': Rpn2, 'Rpx': Rpx,
            'interlength': interlength, 'nl': nl
        }

    def create_sections(self, nodes):
        self.paranodes1 = 2*(nodes-1)   # MYSA paranodes
        self.paranodes2 = 2*(nodes-1)   # FLUT paranodes
        self.axoninter = 6*(nodes-1)    # STIN internodes

        for i in range(self.axonnodes):
            self.node.append(h.Section(name='node[%d]' % i, cell=self))

        for i in range(self.paranodes1):
            self.MYSA.append(h.Section(name='MYSA[%d]' % i, cell=self))

        for i in range(self.paranodes2):
            self.FLUT.append(h.Section(name='FLUT[%d]' % i, cell=self))

        for i in range(self.axoninter):
            self.STIN.append(h.Section(name='STIN[%d]' % i, cell=self))

    def build_topology(self, nodes):
        for i in range(nodes-1):
            self.MYSA[2*i].connect(self.node[i])
            self.FLUT[2*i].connect(self.MYSA[2*i])
            self.STIN[6*i].connect(self.FLUT[2*i])
            self.STIN[6*i+1].connect(self.STIN[6*i])
            self.STIN[6*i+2].connect(self.STIN[6*i+1])
            self.STIN[6*i+3].connect(self.STIN[6*i+2])
            self.STIN[6*i+4].connect(self.STIN[6*i+3])
            self.STIN[6*i+5].connect(self.STIN[6*i+4])
            self.FLUT[2*i+1].connect(self.STIN[6*i+5])
            self.MYSA[2*i+1].connect(self.FLUT[2*i+1])
            self.node[i+1].connect(self.MYSA[2*i+1])

    def define_geometry(self):
        for sec in self.node:
            sec.nseg = 1
            sec.diam = self.nodeD
            sec.L = self.nodelength

        for sec in self.MYSA:
            sec.nseg = 1
            sec.diam = float(self.diameter)
            sec.L = self.paralength1

        for sec in self.FLUT:
            sec.nseg = 1
            sec.diam = float(self.diameter)
            sec.L = self.paralength2

        for sec in self.STIN:
            sec.nseg = 1
            sec.diam = float(self.diameter)
            sec.L = self.interlength

    def define_biophysics(self):
        self.mycm = 0.1    # [uF/cm2]; lemella membrane
        self.mygm = 0.001  # [S/cm2]; lemella membrane
        self.e_pas_Vrest = -80
        diameter = float(self.diameter)

        for sec in self.node:
            sec.Ra = self.rhoa/10000
            sec.cm = 2
            sec.insert('axnode')
            sec.insert('extracellular')
            sec.xraxial[0] = self.Rpn0
            sec.xg[0] = 1e10
            sec.xc[0] = 0

        for sec in self.MYSA:
            self._apply_biophysics(sec, 0.001, self.paraD1, self.Rpn1, diameter)

        for sec in self.FLUT:
            self._apply_biophysics(sec, 0.0001, self.paraD2, self.Rpn2, diameter)

        for sec in self.STIN:
            self._apply_biophysics(sec, 0.0001, self.axonD, self.Rpx, diameter)

    def _apply_biophysics(self, sec, scale, secd, rp, diameter):
        sec.Ra = self.rhoa * (1 / (secd / diameter) ** 2) / 10000
        sec.cm = 2 * secd / diameter
        sec.insert('pas')
        sec.g_pas = scale * secd / diameter
        sec.e_pas = self.e_pas_Vrest
        sec.insert('extracellular')
        sec.xraxial[0] = rp
        sec.xg[0] = self.mygm / (self.nl * 2)
        sec.xc[0] = self.mycm / (self.nl * 2)

    def init_voltages(self):
        for sec in self.all:
            sec.v = self.v_init
