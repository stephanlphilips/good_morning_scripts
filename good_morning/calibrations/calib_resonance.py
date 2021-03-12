from pulse_templates.coherent_control.single_qubit_gates.phase_offsets_charac import phase_offset_charac
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.fit_resonance import fit_resonance
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

def res_calib(target, plot=False):
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
	old_freq = getattr(var_mgr, f'frequency_q{target}')
	gate_set.X180.add(s.manip, f_qubit = linspace(old_freq*1e9-10e6, old_freq*1e9+10e6, 100, axis= 0, name='freq', unit='Hz'))
	s.wait(100).add(s.manip)
	s.read(target)

	sequence, minstr, name = run_qubit_exp(f'frequency_cal_q{target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()

	frequency = ds(f'read{target}').x()
	probabilities = ds(f'read{target}').y()
	resonance = fit_resonance(frequency, probabilities, plot=plot)
	var_mgr = variable_mgr()

	old_res = getattr(var_mgr, f'frequency_q{target}')
	setattr(var_mgr, f'frequency_q{target}', round(resonance*1e-9,6))

	print(f'calibrated resonance for qubit {target}, '+
		f'Old resonance : {round(old_res,6)} \n New resonance : {round(resonance*1e-9,6)} \n')
