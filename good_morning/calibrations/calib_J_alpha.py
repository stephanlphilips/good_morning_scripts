from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from pulse_templates.coherent_control.two_qubit_gates.cphase import cphase_basic

from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import pulse_lib.segments.utility.looping as lp
from good_morning.fittings.fit_rabi_osc import fit_ramsey
from good_morning.fittings.J_versus_voltage import fit_J, J_to_voltage, voltage_to_J

import qcodes as qc
import numpy as np

import good_morning.static.J12 as J12
import good_morning.static.J23 as J23
import good_morning.static.J34 as J34
import good_morning.static.J45 as J45
import good_morning.static.J56 as J56

def calib_J_alpha(target, plot=False):
	'''
	calibrates a single qubit phase for a target qubit

	Args:
		target (int) : qubit pair to target
	'''
	var_mgr = variable_mgr()
	s = six_dot_sample(qc.Station.default.pulse)

	target = str(int(target))
	s.init(target[0], target[1])

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	gates = globals()[f'J{target}'].gates
	N_J = 5
	voltages_gates = globals()[f'J{target}'].voltages_gates
	voltages_gates=list(voltages_gates)
	sweep_gate = lp.linspace(voltages_gates[2*(int(target[0]))]/2,voltages_gates[2*(int(target[0]))], N_J, axis=1, name=f'vB{target[0]}', unit='mV') 
	voltages_gates[2*(int(target[0]))] = sweep_gate
	voltages_gates=tuple(voltages_gates)

	gate_time = lp.linspace(0,getattr(var_mgr, f'time_{target}')*10, 80, axis=0, name='time', unit='ns')
	
	getattr(s,f'q{target[0]}').X90.add(s.manip)
	cphase_basic(s.manip, gates, tuple([0]*len(gates)), voltages_gates, t_gate= gate_time/2, t_ramp=100)
	getattr(s,f'q{target[0]}').X180.add(s.manip)
	getattr(s,f'q{target[1]}').X180.add(s.manip)
	cphase_basic(s.manip, gates, tuple([0]*len(gates)), voltages_gates, t_gate= gate_time/2, t_ramp=100)
	getattr(s,f'q{target[0]}').X90.add(s.manip)

	s.wait(100).add(s.manip)

	s.read(target[0], target[1])

	sequence, minstr, name = run_qubit_exp(f'J_V cal :: {target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()


	time = ds(f'read{target[0]}').y()*1e-9
	probabilities = ds(f'read{target[0]}').z()
	J_meas=[]
	for i in range(N_J):
		time_fit = time[5:]
		probabilities_fit = probabilities[i][5:]
		J_meas += [1/(fit_ramsey(time_fit, probabilities_fit, plot=plot)*2)*1e9]
	barrier_percentage = sweep_gate.data/sweep_gate.data.max()
	J_V_off, J_max, alpha = fit_J(barrier_percentage, np.array(J_meas), plot=plot)

	if not hasattr(var_mgr,f'J_V_off{target}'):
		var_mgr.add_variable(f'cphase{target}',f'J_V_off{target}', 'mV',0.1,0)
	if not hasattr(var_mgr,f'J_max{target}'):
		var_mgr.add_variable(f'cphase{target}',f'J_max{target}', 'mV',0.1,0)
	if not hasattr(var_mgr,f'J_alpha{target}'):
		var_mgr.add_variable(f'cphase{target}',f'J_alpha{target}', 'mV',0.1,0)		
	setattr(var_mgr,f'J_V_off{target}', round(J_V_off,3))
	setattr(var_mgr,f'J_max{target}', round(J_max,3))
	setattr(var_mgr,f'J_alpha{target}', round(alpha,3))

	# return J_off
