from pulse_templates.coherent_control.single_qubit_gates.phase_offsets_charac import phase_offset_charac
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.fit_rabi_osc import fit_ramsey
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import qcodes as qc
import numpy as np
from pulse_lib.segments.utility.looping import linspace

def get_target(obj, name):
	name = name.split('.')

	for operator in name:
		obj = getattr(obj, operator)
	
	return obj

def Pi_calib(target, plot=False):
	'''
	calibrates a single qubit phase for a target qubit

	Args:
		target (int) : qubit number to target (1-6)
		ancillary (list) : qubit that need to be initialized to make this work
	'''
	s = six_dot_sample(qc.Station.default.pulse)
	var_mgr = variable_mgr()

	s.init(target)

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	gate_set = getattr(s, f'q{target}')
	old_pi = getattr(var_mgr, f'pi_q{target}_m3dbm')
	gate_set.X90.add(s.manip, t_pulse = linspace(0,old_pi*4, 60, 'time', 'ns', 0))
	s.wait(100).add(s.manip)
	s.read(target)

	sequence, minstr, name = run_qubit_exp(f'Pi_cal_q{target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()

	time = ds(f'read{target}').x()*1e-9
	probabilities = ds(f'read{target}').y()
	time = time[5:]
	probabilities = probabilities[5:]
	Pi_time = fit_ramsey(time, probabilities, plot=plot)
	var_mgr = variable_mgr()

	old_Pi = getattr(var_mgr, f'pi_q{target}_m3dbm')
	setattr(var_mgr, f'pi_q{target}_m3dbm', round(Pi_time,6))

	print(f'calibrated resonance for qubit {target}, '+
		f'Old resonance : {round(old_Pi,6)} \n New resonance : {round(Pi_time,6)} \n')
