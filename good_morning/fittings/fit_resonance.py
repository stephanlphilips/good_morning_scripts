import matplotlib.pyplot as plt
import numpy as np

import lmfit

def gauss_peak_function(pars, x, data=None):
	amp = pars['amp'].value
	off = pars['off'].value
	f_res = pars['f_res'].value
	linewidth = pars['linewidth'].value

	model = off + amp*np.exp(-((x-f_res)**2)/(2*linewidth**2))

	if data is None:
		return model
	return (model - data)    

def fit_resonance_raw(frequency,probability):
	fit_params = lmfit.Parameters()

	fit_params.add('amp', value=2*round(((np.max(probability)+np.min(probability))/2-np.mean(probability)),1), max=1, min=-1)
	fit_params.add('off', value=np.average(probability), max=1.0, min=0.0)
	if (np.max(probability)+np.min(probability))/2-np.average(probability)>0:
		fit_params.add('f_res', value=frequency[np.argmax(probability)])
	else:
		fit_params.add('f_res', value=frequency[np.argmin(probability)])
	fit_params.add('linewidth', value=1e6)

	mini = lmfit.Minimizer(gauss_peak_function, fit_params, fcn_args=(frequency,), fcn_kws={'data': probability})
	intermedediate_result = mini.minimize(method='Nelder')
	result = mini.minimize(method='leastsq', params=intermedediate_result.params)

	confidence_intervals = None# lmfit.conf_interval(mini, result, verbose=False)
	
	return result, confidence_intervals

def fit_resonance(frequency,probability, plot=False):
	'''
	fit resonance:
	Args:
		frequency (np.ndarray) : GHz
		probability (np.ndarray) : spin prob
	'''	
	fit_result, confidence_interval = fit_resonance_raw(frequency, probability)

	print(f'res freq = {round(fit_result.params["f_res"].value*1e-9, 6)} GHz')
	if plot==True:
		plt.figure()
		plt.plot(frequency, probability, label='original data')
		plt.plot(frequency, gauss_peak_function(fit_result.params, frequency), label='fitted data')
		plt.xlabel('frequency (GHz)')
		plt.ylabel(('spin probability (%)'))
		plt.legend()
		plt.show()

	return fit_result.params['f_res'].value


if __name__ == '__main__':
	from core_tools.data.SQL.connect import set_up_local_storage
	set_up_local_storage("xld_user", "XLDspin001", "vandersypen_data", "6dot", "XLD", "6D2S - SQ21-XX-X-XX-X")

	from core_tools.data.ds.data_set import load_by_id
	ds = load_by_id(16728)
	data = ds('read12')
	print(data)
	x = data.x()
	y = data.y()
	print(x, y)
	fit_resonance(x, y, True)