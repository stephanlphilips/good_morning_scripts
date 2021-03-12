import pulse_lib.segments.utility.looping as lp
import qcodes as qc
import matplotlib.pyplot as plt
from pulse_templates.oper.operators import wait
from dev_V2.PSB_4_qubit_3153.OPER import do_MANIP
from pulse_templates.psb_pulses.readout_pulses import PSB_read_multi

from dev_V2.Elzerman_2_qubits_clean.TRIG import mk_TRIG
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_PSB_exp
from dev_V2.PSB_4_qubit_3153.VAR import variables
from core_tools.sweeps.sweeps import scan_generic
import scipy as sp
import numpy as np

from dev_V2.six_qubit_QC.system import six_dot_sample
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_qubit_exp

def PSB12_calibration(plot=False, verbose = False):
    gates, _311113, ST_anti_12, ST_anti_12_tc_high, ST_anti_56, vSD1_threshold, vSD2_threshold = variables()
    var_mgr = variable_mgr()
    anticrossing = ST_anti_12

    s = six_dot_sample(qc.Station.default.pulse)
    s.init12.add(sweep_range = 1)
    s.manip.qubit1_MW.add_chirp(0, 50e3, var_mgr.frequency_q1*1e9-5e6, var_mgr.frequency_q1*1e9+5e6, 300)
    s.read12.add(sweep_range = 1)
    s.measurement_manager.n_rep = 500
    sequence, minstr, name = run_qubit_exp(f'PSB12_calibration', s.segments(), s.measurement_manager)

    qc.Station.default.MW_source.on()    
    ds_on = scan_generic(sequence, minstr, name=name).run()
    qc.Station.default.MW_source.off()
    ds_off = scan_generic(sequence, minstr, name=name).run()

    x = ds_on('read12').x()
    y = ds_on('read12').y()
    contrast = ds_on('read12')() -  ds_off('read12')()  
    contrast = sp.ndimage.filters.gaussian_filter(contrast, [2,2], mode='constant')
    if plot:
        plt.imshow(contrast)
        
    var_mgr.PSB_12_P2 = round(x[np.where(contrast == contrast.max())[0][0]], 2)
    var_mgr.PSB_12_P1 = round(y[np.where(contrast == contrast.max())[1][0]], 2)

    print(f"Selected point\n\tvP1 :: {var_mgr.PSB_12_P1}\n\tvP2 :: {var_mgr.PSB_12_P2}")

    qc.Station.default.MW_source.on()        
    return None

def PSB56_calibration(station, plot=False, verbose = False):
    gates, _311113, ST_anti_12, ST_anti_12_tc_high, ST_anti_56, vSD1_threshold, vSD2_threshold = variables()
    var_mgr = variable_mgr()
    anticrossing = ST_anti_56

    s = six_dot_sample(qc.Station.default.pulse)
    s.init56.add(sweep_range = 1)
    s.manip.qubit6_MW.add_chirp(0, 50e3, var_mgr.frequency_q6*1e9-5e6, var_mgr.frequency_q6*1e9+5e6, 300)
    s.read56.add(sweep_range = 1)
    s.measurement_manager.n_rep = 500
    sequence, minstr, name = run_qubit_exp(f'PSB56_calibration', s.segments(), s.measurement_manager)

    station.MW_source.on()    
    ds_on = scan_generic(sequence, minstr, name=name).run()
    station.MW_source.off()    
    ds_off = scan_generic(sequence, minstr, name=name).run()

    x = ds_on('read56').x()
    y = ds_on('read56').y()    
    contrast = ds_on('read56')() - ds_off('read56')()

    contrast = sp.ndimage.filters.gaussian_filter(contrast, [2,2], mode='constant')
    if plot:
        plt.imshow(contrast)

    var_mgr.PSB_56_P5 = round(x[np.where(contrast == contrast.max())[0][0]],2)
    var_mgr.PSB_56_P6 = round(y[np.where(contrast == contrast.max())[1][0]],2)
    print(f"Selected point\n\tvP5 :: {var_mgr.PSB_56_P5}\n\tvP6 :: {var_mgr.PSB_56_P6}")

    station.MW_source.on()        
    return None


    # pulse = qc.Station.default.pulse

    # TRIG = mk_TRIG()
    # MANIP = do_MANIP(True)
    # wait(MANIP, gates,  1e3, _311113)
    # MANIP.qubit6_MW.add_chirp(0, 30e3, var_mgr.frequency_q6*1e9-5e6, var_mgr.frequency_q6*1e9+5e6, 300)
    # MANIP.reset_time()
    # wait(MANIP, gates, 10e3, _311113)
    # READ_1 = pulse.mk_segment()
    # READ_2 = pulse.mk_segment()

    # anticrossing = list(anticrossing)
    # anticrossing[9] = lp.linspace(anticrossing[9] - 0.5 ,anticrossing[9] + 0.5, 15, axis=1, name='vP5', unit='mV') 
    # anticrossing[11] = lp.linspace(anticrossing[11] - 0.5 ,anticrossing[11] + 0.5, 15, axis=0, name='vP6', unit='mV')
    # anticrossing =tuple(anticrossing)

    # PSB_read_multi(READ_1, gates, 2e3, 2e3, _311113, anticrossing, 1, unmute='M_SD2')
    # PSB_read_multi(READ_2, gates, 2e3, 2e3, _311113, anticrossing, 2, unmute='M_SD2')
    
    # n_rep = 500    
    # seq = [TRIG, READ_1, MANIP, READ_2]  

    # sequence, minstr, name = run_PSB_exp('PSB56_calibration', seq, 2e3, n_rep, 2, False, phase=[var_mgr.RF_readout_phase, var_mgr.RF_readout_phase_SD2], order=[2,2], threshold=[var_mgr.vSD2_threshold, var_mgr.vSD2_threshold])
    