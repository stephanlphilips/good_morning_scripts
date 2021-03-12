from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.fit_symmetry import fit_symmetry
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import pulse_lib.segments.utility.looping as lp
from good_morning.fittings.J_versus_voltage import fit_J, J_to_voltage
from pulse_templates.coherent_control.two_qubit_gates.standard_set import two_qubit_gate_generic
from pulse_templates.coherent_control.two_qubit_gates.cphase import cphase_basic
import qcodes as qc
import numpy as np
import good_morning.static.J12 as J12
import good_morning.static.J23 as J23
import good_morning.static.J34 as J34
import good_morning.static.J45 as J45
import good_morning.static.J56 as J56


def calib_symm_point(target, even=False, plot=False):
	'''
	Args:
		qubit_pair (str) : pair of qubits to calibrate cphase for.
	'''
	s = six_dot_sample(qc.Station.default.pulse)
	var_mgr = variable_mgr()
	J_off_volt = (0,0, 0,0, 0,0, 0,0, 0,0, 0,0)

	time = getattr(var_mgr, f'time_{target}')
	target = str(int(target))
	s.init(target[0], target[1])
	gates = globals()[f'J{target}'].gates	
	voltages_gates = globals()[f'J{target}'].voltages_gates
	voltages_gates=list(voltages_gates)
	sweep_gate = lp.linspace(-6,6, 51, axis=0, name=f'vP{target[0]}', unit='mV') 
	step_gate = lp.linspace(-6,6, 51, axis=1, name=f'vP{target[1]}', unit='mV') 
	voltages_gates[2*(int(target[0])-1)+1] = sweep_gate
	voltages_gates[2*(int(target[1])-1)+1] = step_gate	
	voltages_gates=tuple(voltages_gates)
	cphase = two_qubit_gate_generic(cphase_basic, {'gates' : gates, 
                                    'v_exchange_pulse_off' : J_off_volt,
                                    'v_exchange_pulse_on' : voltages_gates,
                                    't_gate' : time,
                                    't_ramp' : 20},
                 {})

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	getattr(s,f'q{target[0]}').X90.add(s.manip)
	cphase.add(s.manip)
	getattr(s,f'q{target[0]}').X180.add(s.manip)
	getattr(s,f'q{target[1]}').X180.add(s.manip)
	cphase.add(s.manip)
	getattr(s,f'q{target[0]}').X90.add(s.manip)

	s.wait(100).add(s.manip)

	s.read(target[0])

	sequence, minstr, name = run_qubit_exp(f'symm cal :: {target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()

	x_axis = ds(f'read{target[0]}').x()
	y_axis = ds(f'read{target[0]}').y()
	probabilities = ds(f'read{target[0]}').z()
	fit_symmetry(x_axis,y_axis,probabilities, plot)