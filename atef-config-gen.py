from atef.config import PVConfiguration
from atef.check import Equals
import json
from ophyd import Component as Cpt                                                                                                    
from ophyd import Device, EpicsSignal, EpicsSignalRO                                                                                  
from pcdsdevices.interface import BaseInterface  

class OpticsHard(BaseInterface, Device):                                                                                                    
    pos_lag_time = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagTime_RBV')                                                                      
    pos_lag_mon_val = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagVal_RBV')     
    plc_soft_limit_min = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMin_RBV' )
    plc_soft_limit_max = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMax_RBV')
    enc_offset = Cpt(EpicsSignal, ':PLC:AxisPar:EncOffset_RBV')
    enc_scale = Cpt(EpicsSignal, ':PLC:AxisPar:EncScaling_RBV')
    pos_lag_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagEn_RBV')
    max_plc_limit_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMaxEn_RBV')
    min_plc_limit_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMinEn_RBV')

beamline = "RIX"
devices = ["MR1K1:BEND:MMS:PITCH", "MR2K2:FLAT:MMS:PITCH", "MR3K2:KBH:MMS:PITCH", "MR4K2:KBV:MMS:PITCH"] 

f = open("Scratch-Auto-Atef.json", "r")
p = json.loads(f.read())
f.close()

#oh = OpticsHard("MR3K2:KBH:MMS:X", name="mr3k2")

for device in devices:
    oh = OpticsHard(device, name="")
    #current_config = oh.get()

    for tup in oh.get_instantiated_signals():
        print(tup[0])
        print(tup[1].read_pv)
        print(tup[1].get())
        print("")
    
        

print(oh.pos_lag_enabled.get())
print(oh.enc_scale.get())
#for config in p['root']['configs']:
    #print(config['PVConfiguration']['name'])
    #print(PVConfiguration(**config['PVConfiguration']))
