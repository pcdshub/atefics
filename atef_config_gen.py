from atef.config import ConfigurationFile, ConfigurationGroup, Configuration, PVConfiguration
from atef.check import Equals
import json
from ophyd import Component as Cpt                                                                                                    
from ophyd import Device, EpicsSignal, EpicsSignalRO                                                                                  
from pcdsdevices.interface import BaseInterface  
import apischema

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


def addEqualComparison(file, config_name, axis_name, pv, value, name="", description="", overwrite=False):
    """Given an ATEF ConfiurationFile, find the specified PVConfiguration,
    create and insert a new Equal comparison into the PVConfiguration.

    Args:
        file (String): The atef config file.
        config_name (String): The configuration to looks for.
        axis_name (String): The axis to add the comparison to. 
        pv (String): The PV name used to conduct the comparison. 
        value (Any): The value to compare to.
    """
    comparison = apischema.serialize(Equals(value=value, name=name, description=description))

    with open("scratch.json", "r") as fd:
        configFile = json.loads(fd.read())

    foundConfig = False
    for config in configFile['root']['configs']:
        if config['ConfigurationGroup']['name'] == config_name:
            print("found Configuration Group")
            foundConfig = True
            for axis in config['ConfigurationGroup']['configs']:
                print(axis['PVConfiguration']['name'])
                
                if axis['PVConfiguration']['name'] == axis_name:
                    by_pv = axis['PVConfiguration']['by_pv']
                    print("found Axis Configuration")

                    if pv in by_pv and overwrite:
                        del by_pv[pv]
                        by_pv[pv] = [{"Equals": comparison}]
                    elif pv not in by_pv:
                        by_pv[pv] = [{"Equals": comparison}]
                    break
        if foundConfig:
            break
    
    with open("scratch.json", "w") as fd:
        fd.write(json.dumps(configFile))

def addCurrentAxisParameters(file, mirror, base_pv_axis, axis, overwrite=False):
    hardstop_config = OpticsHard(base_pv_axis, name='')
    signals = hardstop_config.get_instantiated_signals()
    for signal in signals:
        if signal[1].name == "_pos_lag_time":
            name = axis + " Pos Lag Time"
            description = "Maximum allowable duration outside of maximum position lag value in seconds."
            value = hardstop_config.pos_lag_time.get()
            pv = hardstop_config.pos_lag_time.pvname

        elif signal[1].name == "_pos_lag_mon_val":
            name = axis + " Pos Lag Monitoring Val"
            description = "Maximum magnitude of position lag in EU."
            value = hardstop_config.pos_lag_mon_val.get()
            pv = hardstop_config.pos_lag_mon_val.pvname

        elif signal[1].name == "_plc_soft_limit_min":
            name = axis + " PLC Soft Limit Min"
            description = "Minimum commandable position of the axis in EU."
            value = hardstop_config.plc_soft_limit_min.get()
            pv = hardstop_config.plc_soft_limit_min.pvname

        elif signal[1].name == "_plc_soft_limit_max":
            name = axis + " PLC Soft Limit Max"
            description = "Maximum commandable position of the axis in EU."
            value = hardstop_config.plc_soft_limit_max.get()
            pv = hardstop_config.plc_soft_limit_max.pvname

        elif signal[1].name == "_enc_offset":
            name = axis + " Encoder Offset"
            description = "Encoder scaling numerator / denominator in EU/COUNT."
            value = hardstop_config.enc_offset.get()
            pv = hardstop_config.enc_offset.pvname
        elif signal[1].name == "_enc_scale":
            name = axis + " Enc Scale"
            description = "Encoder scaling numerator / denominator in EU/COUNT."
            value = hardstop_config.enc_scale.get()
            pv = hardstop_config.enc_scale.pvname
        elif signal[1].name == "_pos_lag_enabled":
            name= axis + " Pos Lag Mon Enabled"
            description  = "Enable/Disable state of Position Lag Monitor."
            value = hardstop_config.pos_lag_enabled.get()
            pv = hardstop_config.pos_lag_enabled.pvname
        elif signal[1].name == "_max_plc_limit_enabled":
            name = axis + " Max PLC Limit Enabled"
            description = "Enable/Disable state of controller static maximum limit"
            value = hardstop_config.max_plc_limit_enabled.get()
            pv = hardstop_config.max_plc_limit_enabled.pvname
        elif signal[1].name == "_min_plc_limit_enabled":
            name = axis + " Min PLC Limit Enabled"
            description = "Enable/Disable state of controller static minimum limit"
            value = hardstop_config.min_plc_limit_enabled.get()
            pv = hardstop_config.min_plc_limit_enabled.pvname
        addEqualComparison(file, mirror, axis, pv, value, name, description, overwrite)

#addCurrentAxisParameters("scratch.json", "MR2K2 FLAT", "MR2K2:FLAT:MMS:Y", "Y", True) 
addCurrentAxisParameters("scratch.json", "MR2K2 FLAT", "MR2K2:FLAT:MMS:PITCH", "Pitch", True) 
#addCurrentAxisParameters("scratch.json", "MR3K2 KBH", "MR2K2:FLAT:MMS:PITCH", "Pitch", True) 
addCurrentAxisParameters("scratch.json", "MR3K2 KBH", "MR2K2:FLAT:MMS:X", "X", True) 
addCurrentAxisParameters("scratch.json", "MR3K2 KBH", "MR2K2:FLAT:MMS:Y", "Y", True) 




#addEqualComparison("test_file", "MR2K2 FLAT", "Y", "MR2K2:TEST2:PV", 8)

#e = Equals(value=8.0)
#print(apischema.serialize(Equals, e))



    
        



#addEqualComparison()



'''
configFile = ConfigurationFile(**p)
configFile.root = ConfigurationGroup(**configFile.root)

newConfigs = []
newBy_pv = {}

for config in configFile.root.configs:
    newConfigs.append(PVConfiguration(**config['PVConfiguration']))
for config in newConfigs:
    d = config.by_pv
    for k, v in d.items():
        for comparison in d[k]:
            newBy_pv['k'] = Equals(**comparison['Equals']) 
    config.by_pv = newBy_pv
    newBy_pv = {}

configFile.root.configs = newConfigs

with open("new_test_file", "w") as fd:
    serialized = apischema.serialize(ConfigurationFile, configFile)
    fd.write(json.dumps(serialized))


#print(config.root.children())
#print(type(config))

print(type(configFile.root))
print(configFile.version)
'''

    #print(config['PVConfiguration']['name'])
    #print(PVConfiguration(**config['PVConfiguration']))

#oh = OpticsHard("MR3K2:KBH:MMS:X", name="mr3k2")

#for device in devices:
#    oh = OpticsHard(device, name="")
#    #current_config = oh.get()
#
#    for tup in oh.get_instantiated_signals():
#        print(tup[0])
#        print(tup[1].read_pv)
#        print(tup[1].get())
#        print("")
    
        

#print(oh.pos_lag_enabled.get())
#print(oh.enc_scale.get())
