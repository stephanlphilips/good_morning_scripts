import pulse_lib.segments.utility.looping as lp
import qcodes as qc
from dev_V2.PSB_4_qubit_3153.OPER import PSB_read_multi_12
from dev_V2.Elzerman_2_qubits_clean.TRIG import mk_TRIG
from core_tools.utility.variable_mgr.var_mgr import variable_mgr
from core_tools.sweeps.pulse_lib_wrappers.PSB_exp import run_PSB_exp
from pulse_templates.psb_pulses.readout_pulses import PSB_read_multi
from dev_V2.PSB_4_qubit_3153.VAR import variables
from core_tools.sweeps.sweeps import scan_generic

def SD1_calibration(verbose = False):
    gates, _311113, ST_anti_12, ST_anti_12_tc_high, ST_anti_56, vSD1_threshold, vSD2_threshold = variables()
    anticrossing = ST_anti_12

    pulse = qc.Station.default.pulse
    TRIG = mk_TRIG()
    EMPTY = pulse.mk_segment()
    var_mgr = variable_mgr()
    
    anticrossing = list(anticrossing)
    anticrossing[1] = lp.linspace(anticrossing[1] -1,anticrossing[1] + 1, 2, axis=1, name='vP1', unit='mV') 
    anticrossing[12] = lp.linspace(anticrossing[12] - 3,anticrossing[12] + 3, 80, axis=0, name='vSD1', unit='mV')
    anticrossing =tuple(anticrossing)

    PSB_read_multi_12(EMPTY, gates, 10, 2e3, _311113, anticrossing, 1)

    seq = [TRIG, EMPTY]

    raw_trace = False
    t_meas = 2e3
    n_qubit = 1
    n_rep = 500

    sequence, minstr, name = run_PSB_exp('SD1_calibration', seq, t_meas, n_rep, n_qubit, raw_trace, phase=[var_mgr.RF_readout_phase, var_mgr.RF_readout_phase_SD2], order=[1])
    ds = scan_generic(sequence, minstr, name=name).run()
    data = ds.m1a()
    y = ds.m1.y()
    SD1_winner=0
    contrast=0
    threshold=0
    for x in range(50):
        if data[1][x]-data[0][x] > contrast:
            contrast = data[1][x]-data[0][x]
            threshold = (data[1][x]+data[0][x])/2
            SD1_winner = y[x]
    print(SD1_winner)
    var_mgr.SD1_P_on_11 = SD1_winner 
    print(contrast)
    print(threshold)
    var_mgr.vSD1_threshold = threshold 
    return None

def SD2_calibration(verbose = False):
    gates, _311113, ST_anti_12, ST_anti_12_tc_high, ST_anti_56, vSD1_threshold, vSD2_threshold = variables()
    anticrossing = ST_anti_56

    pulse = qc.Station.default.pulse
    TRIG = mk_TRIG()
    EMPTY = pulse.mk_segment()
    var_mgr = variable_mgr()
    
    anticrossing = list(anticrossing)
    anticrossing[11] = lp.linspace(anticrossing[11] - 2,anticrossing[11] + 2, 2, axis=1, name='vP6', unit='mV') 
    anticrossing[13] = lp.linspace(anticrossing[13] - 2,anticrossing[13] + 2, 80, axis=0, name='vSD2', unit='mV')
    anticrossing =tuple(anticrossing)

    PSB_read_multi(EMPTY, gates, 2e3, 2e3, _311113, anticrossing, 1, unmute='M_SD2')

    seq = [TRIG, EMPTY]

    raw_trace = False
    t_meas = 2e3
    n_qubit = 1
    n_rep = 500

    sequence, minstr, name = run_PSB_exp('SD2_calibration', seq, t_meas, n_rep, n_qubit, raw_trace, phase=[var_mgr.RF_readout_phase, var_mgr.RF_readout_phase_SD2], order=[2])
    ds = scan_generic(sequence, minstr, name=name).run()
    data = ds.m1a()
    y = ds.m1.y()
    SD2_winner=0
    contrast=0
    threshold=0
    for x in range(50):
        if data[1][x]-data[0][x] > contrast:
            contrast = data[1][x]-data[0][x]
            threshold = (data[1][x]+data[0][x])/2
            SD2_winner = y[x]
    print(SD2_winner)
    var_mgr.SD2_P_on_11 = SD2_winner 
    print(contrast)
    print(threshold)
    var_mgr.vSD2_threshold = threshold 
    return None
