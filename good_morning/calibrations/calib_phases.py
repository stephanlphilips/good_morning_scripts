from pulse_templates.coherent_control.single_qubit_gates.phase_offsets_charac import phase_offset_charac
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.phase_oscillations import fit_phase
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import qcodes as qc
import numpy as np

def get_target(obj, name):
	name = name.split('.')

	for operator in name:
		obj = getattr(obj, operator)
	
	return obj

def phase_calib(target, ancillary, gate, undo_gate = None, plot=False):
	'''
	calibrates a single qubit phase for a target qubit

	Args:
		target (int) : qubit number to target (1-6)
		ancillary (list) : qubit that need to be initialized to make this work
		gate (str) : name of the gate to call (e.g, q2.X or q12.cphase )
		undo_gate (str) : name of the gate that cancels the previous gate
	'''
	s = six_dot_sample(qc.Station.default.pulse)

	s.init(target, *ancillary)

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	gate_set = getattr(s, f'q{target}')
	phase_offset_charac(s.manip, gate_set, get_target(s,gate))

	s.wait(100).add(s.manip)
	if undo_gate is not None:
		get_target(s,undo_gate).add(s.manip)
	s.wait(100).add(s.manip)

	s.read(target)

	sequence, minstr, name = run_qubit_exp(f'phase_cal_q{target}, target gate : {gate}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()

	input_phases = ds(f'read{target}').x()
	amplitude = ds(f'read{target}').y()

	# get rid of the first part due to heating
	input_phases = input_phases[20:]
	amplitude = amplitude[20:]

	phase, std_error = fit_phase(input_phases, amplitude, plot=plot)

	var_mgr = variable_mgr()

	if not hasattr(var_mgr, f'PHASE_q{target}_{gate.replace(".", "_")}'):
		var_mgr.add_variable(f'Qubit {target}',f'PHASE_q{target}_{gate.replace(".", "_")}','rad',0.1,0)

	old_phase = getattr(var_mgr, f'PHASE_q{target}_{gate.replace(".", "_")}')
	setattr(var_mgr, f'PHASE_q{target}_{gate.replace(".", "_")}', round(phase,3))

	print(f'calibrated phase for qubit {target}, '+
		f'for gate {gate}. \n Old phase : {round(old_phase,2)} \n New Phase : {round(phase,2)} [{round(std_error[0],2)} : {round(std_error[1],2)}]\n')

	return phase
