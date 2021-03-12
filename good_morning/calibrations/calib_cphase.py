from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.phase_oscillations import fit_phase
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import pulse_lib.segments.utility.looping as lp

import qcodes as qc
import numpy as np



def cphase_ZZ_calib(target, even=False, plot=False):
	'''
	Args:
		qubit_pair (str) : pair of qubits to calibrate cphase for.
	'''
	s = six_dot_sample(qc.Station.default.pulse)

	target = str(int(target))
	s.init(target[0], target[1])

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	sweep = lp.linspace(-0.2*np.pi,4*np.pi, 100, 'angle', 'rad', 0)/2

	getattr(s,f'q{target[0]}').X90.add(s.manip)
	getattr(s,f'q{target}').cphase.add(s.manip, cphase_angle=sweep, padding = 30, phase_corrections={})
	getattr(s,f'q{target[0]}').X180.add(s.manip)
	getattr(s,f'q{target[1]}').X180.add(s.manip)
	getattr(s,f'q{target}').cphase.add(s.manip, cphase_angle=sweep, padding = 30, phase_corrections={})
	getattr(s,f'q{target[0]}').X90.add(s.manip)

	s.wait(100).add(s.manip)

	s.read(target[0], target[1])

	sequence, minstr, name = run_qubit_exp(f'cphase cal :: {target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()


	target_ds = target[0]
	input_phases = ds(f'read{target_ds}').x()
	amplitude = ds(f'read{target_ds}').y()

	# get rid of the first part due to heating
	input_phases = input_phases[10:]
	amplitude = amplitude[10:]

	phase, std_error = fit_phase(input_phases, amplitude, plot=plot)

	if even == True:
		cphase_angle = (3*np.pi - phase)/2
	else:
		cphase_angle = (2*np.pi + phase)/2

	var_mgr = variable_mgr()
	setattr(var_mgr, f'J_pi_{target}', cphase_angle)
	
	if not hasattr(var_mgr,f'J_pi_{target}'):
		var_mgr.add_variable(f'cphase{target}',f'J_pi_{target}','rad',0.1,0)

	old_phase = getattr(var_mgr,f'J_pi_{target}')
	setattr(var_mgr,f'J_pi_{target}', round(phase,3))


def cphase_ZI_IZ_cal(pair, target, even=True, plot=False):
	'''
	calibrate single qubit phases.

	args:
		pair   : pair of qubit to calibrate
		target : qubit to target with the cnot
		even   : if initial state is even Flase, else True
	'''

	s = six_dot_sample(qc.Station.default.pulse)

	pair = str(int(pair))
	s.init(pair[0], pair[1])

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	getattr(s, f'q{target}').X90.add(s.manip)
	getattr(s, f'q{pair}').cphase.add(s.manip, padding = 30, phase_corrections={})
	getattr(s, f'q{target}').X90.add(s.manip, phase = lp.linspace(-1,4*np.pi, 80, 'angle', 'rad', 0))

	s.wait(100).add(s.manip)

	s.read(pair[0], pair[1])

	sequence, minstr, name = run_qubit_exp(f'cphase single qubit phase cal :: q{target}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()

	input_phases = ds(f'read{target}').x()
	amplitude = ds(f'read{target}').y()

	# get rid of the first part due to heating
	input_phases = input_phases[10:]
	amplitude = amplitude[10:]

	phase, std_error = fit_phase(input_phases, amplitude, plot=plot)

	phase = -phase
	if even == True:
		phase += np.pi

	var_mgr = variable_mgr()

	if not hasattr(var_mgr, f'PHASE_q{target}_q{pair}_cphase'):
		var_mgr.add_variable(f'cphase{pair}',f'PHASE_q{target}_q{pair}_cphase','rad',0.1,0)

	old_phase = getattr(var_mgr, f'PHASE_q{target}_q{pair}_cphase')
	setattr(var_mgr, f'PHASE_q{target}_q{pair}_cphase', round(phase,3))

	print('setting ' + f'PHASE_q{target}_q{pair}_cphase to {phase}')
