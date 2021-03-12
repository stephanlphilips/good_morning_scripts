from pulse_templates.coherent_control.single_qubit_gates.allXY import generate_all_XY
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp
from good_morning.fittings.allXY import fit_allXY

from core_tools.sweeps.sweeps import scan_generic, do0D, do1D
from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
import qcodes as qc
import numpy as np

NREP = 5

def allXY(qubit, plot=False, nth_iter=0):
	'''
	calibrates a single qubit phase for a qubit

	Args:
		qubit (int) : qubit number to target (1-6)
		plot (bool) : plot the allXY fitting
		nth_iter (int) : nth itheration this script is called
	'''
	if nth_iter > 5:
		raise ValueError(f'failed to reach convergence on the allXX of qubit {qubit}')

	pulse_length_increment, off_resonance_error = _allXY_(qubit, plot)

	var_mgr = variable_mgr()
	setattr(var_mgr, f'pi_q{qubit}_m3dbm', round(getattr(var_mgr, f'pi_q{qubit}_m3dbm')*(1+pulse_length_increment), 1))
	freq = getattr(var_mgr, f'frequency_q{qubit}') + off_resonance_error*1e-9
	setattr(var_mgr, f'frequency_q{qubit}', freq)
	
	if abs(off_resonance_error) < 100e3 and abs(pulse_length_increment) < 0.005:
		return None
	else:
		return allXY(qubit, plot, nth_iter+1)

def _allXY_(qubit, plot=False):
	s = six_dot_sample(qc.Station.default.pulse)

	s.init(qubit)

	s.wait(500).add(s.manip)
	s.pre_pulse.add(s.manip)

	s.wait(1000).add(s.manip)
	generate_all_XY(s.manip, getattr(s, f'q{qubit}'), repeat=NREP)
	s.wait(1000).add(s.manip)

	s.read(qubit)

	sequence, minstr, name = run_qubit_exp(f'allXY qubit {qubit}', s.segments(), s.measurement_manager)
	ds = scan_generic(sequence, minstr, name=name).run()
	amplitude = np.average(np.reshape(ds(f'read{qubit}').y(), (NREP,21)), axis=0)

	var_mgr = variable_mgr()
	pulse_length_increment, off_resonance_error = fit_allXY(amplitude, getattr(var_mgr, f'pi_q{qubit}_m3dbm')*1e-9, plot=plot)
	return pulse_length_increment, off_resonance_error