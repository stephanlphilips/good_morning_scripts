from good_morning.fittings.J_versus_voltage import fit_J, J_to_voltage
from core_tools.utility.variable_mgr.var_mgr import variable_mgr

gates  = ('vB0','vP1', 'vB1','vP2', 'vB2','vP3', 'vB3','vP4', 'vB4','vP5', 'vB5','vP6')
voltages_gates = (-80,0, -80,0, -80,0, -100,variable_mgr().symm45_P4, variable_mgr().B4_45,variable_mgr().symm45_P5, -100,0)

J_off = 0.022917827490600135
J_max = 4306.648735663147
alpha = 3.7242883106110556

def return_scalled_barier(voltage):
	def barrier(J):
		return voltage*J_to_voltage(J, variable_mgr().J_V_off45, variable_mgr().J_max45, variable_mgr().J_alpha45)
	return barrier

def gen_J_to_voltage():
	barriers = []
	for gate, voltage in zip(gates, voltages_gates):
		barriers += [return_scalled_barier(voltage)]
	return barriers


if __name__ == '__main__':
	import numpy as np
	barrier_percentage = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
	J_effective = np.array([10e3, 20e3, 28e3, 40e3, 110e3, 0.18e6, 0.42e6, 0.96e6,  1.84e6, 4.3e6, 8.74e6 ])
	
	J_off, J_max, alpha = fit_J(barrier_percentage, J_effective, True)
	print(J_off, J_max, alpha)