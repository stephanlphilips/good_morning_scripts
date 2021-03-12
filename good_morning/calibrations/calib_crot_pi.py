from pulse_templates.coherent_control.single_qubit_gates.phase_offsets_charac import phase_offset_charac
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.fit_rabi_osc import fit_ramsey
from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import qcodes as qc
import numpy as np
from pulse_lib.segments.utility.looping import linspace
from pulse_templates.coherent_control.single_qubit_gates.single_qubit_gates import single_qubit_gate_spec

def get_target(obj, name):
	name = name.split('.')

	for operator in name:
		obj = getattr(obj, operator)
	
	return obj

def CROT_cali_pi_meas(pair, target, ancilla, freqs, old_time, flip):

	s = six_dot_sample(qc.Station.default.pulse)
	var_mgr = variable_mgr()

	pair = str(int(pair))
	s.init(pair[0], pair[1])

	s.wait(100).add(s.manip)
	s.pre_pulse.add(s.manip)
	s.wait(100).add(s.manip)

	gate_set = getattr(s, f'q{pair}')
	target_gate_set = getattr(s, f'q{pair[target-1]}')
	ancilla_gate_set = getattr(s, f'q{pair[ancilla-1]}')

	if flip:
		ancilla_gate_set.X180.add(s.manip)
		# target_gate_set.X180.add(s.manip)

	scan_range = single_qubit_gate_spec(f'qubit{target}_MW', 
                                    linspace(freqs[0]*1e9, freqs[1]*1e9, 2, axis= 1, name='freq', unit='Hz'),
                                    linspace(0,old_time*4, 100, axis= 0, name='time', unit='ns'), getattr(var_mgr, f'q{pair[target-1]}_MW_power'), padding=2)

	gate_to_test = getattr(gate_set, f'CROT{target}{ancilla}')

	gate_to_test.add(s.manip, gate_spec = scan_range)
	s.wait(100).add(s.manip)
	s.read(pair[target-1])
	sequence, minstr, name = run_qubit_exp(f'crot-z_crot_cal_pi_q{pair}_target{pair[target-1]}', s.segments(), s.measurement_manager)

	return sequence, minstr, name

def CROT_pi_calib(pair, target, ancilla, plot=False):
	'''
	calibrates a single qubit phase for a target qubit

	Args:
		target (int) : qubit number to target (1-6)
		ancillary (list) : qubit that need to be initialized to make this work
	'''
	var_mgr = variable_mgr()
	pair = str(int(pair))

	old_crot = getattr(var_mgr, f'crot{pair[target-1]}{pair[ancilla-1]}')
	old_z_crot = getattr(var_mgr, f'z_crot{pair[target-1]}{pair[ancilla-1]}')
	crot_time = getattr(var_mgr, f'pi_crot{pair[target-1]}_m3dbm')
	z_crot_time = getattr(var_mgr, f'pi_z_crot{pair[target-1]}_m3dbm')

	gate_time= max(crot_time,z_crot_time)	

	sequence, minstr, name = CROT_cali_pi_meas(pair, target, ancilla, [old_z_crot,old_crot], gate_time, 0)
	ds_one = scan_generic(sequence, minstr, name=name).run()
	sequence, minstr, name = CROT_cali_pi_meas(pair, target, ancilla, [old_z_crot,old_crot], gate_time, 1)
	ds_two = scan_generic(sequence, minstr, name=name).run()

	frequency_one = ds_one(f'read{pair[target-1]}').x()
	time_one = ds_one(f'read{pair[target-1]}').y()*1e-9
	probabilities_one = ds_one(f'read{pair[target-1]}').z()
	index_one = np.argmax([[np.std(probabilities_one[0]),np.std(probabilities_one[1])]])
	Pi_time_one = fit_ramsey(time_one[5:], probabilities_one[index_one][5:], plot=plot)
	
	frequency_two = ds_two(f'read{pair[target-1]}').x()
	time_two = ds_two(f'read{pair[target-1]}').y()*1e-9
	probabilities_two = ds_two(f'read{pair[target-1]}').z()
	index_two = np.argmax([[np.std(probabilities_two[0]),np.std(probabilities_two[1])]])
	Pi_time_two = fit_ramsey(time_two, probabilities_two[index_two], plot=plot)

	if index_one>index_two:
		pi_crot =[Pi_time_two,Pi_time_one]
	else:
		pi_crot =[Pi_time_one,Pi_time_two]
	old_z_crot = getattr(var_mgr, f'pi_z_crot{pair[target-1]}_m3dbm')
	setattr(var_mgr, f'pi_z_crot{pair[target-1]}_m3dbm', round(pi_crot[0]))
	old_crot = getattr(var_mgr, f'pi_crot{pair[target-1]}_m3dbm')
	setattr(var_mgr, f'pi_crot{pair[target-1]}_m3dbm', round(pi_crot[1]))

	print(f'calibrated z_crot_pi for qubit pair {pair}, target {pair[target-1]} '+
		f'Old z_crot_pi : {round(old_z_crot,6)} \n New z_crot_pi : {round(pi_crot[0])} \n')
	print(f'calibrated crot_pi for qubit pair {pair}, target {pair[target-1]} '+
		f'Old crot_pi : {round(old_crot,6)} \n New crot_pi : {round(pi_crot[1])} \n')