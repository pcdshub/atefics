from atef.config import ConfigurationFile, ConfigurationGroup, PVConfiguration
from atef.check import Equals
import json
from ophyd import Component as Cpt                                                                                                    
from ophyd import Device, EpicsSignal 
from pcdsdevices.interface import BaseInterface  
import apischema


class OpticsHard(BaseInterface, Device):                                                                                                    
    pos_lag_time = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagTime_RBV', doc="Maximum allowable duration outside of maximum position lag value in seconds.")
    pos_lag_mon_val = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagVal_RBV', doc="Maximum magnitude of position lag in EU.")     
    plc_soft_limit_min = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMin_RBV', doc="Minimum commandable position of the axis in EU." )
    plc_soft_limit_max = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMax_RBV', doc="Maximum commandable position of the axis in EU.")
    enc_offset = Cpt(EpicsSignal, ':PLC:AxisPar:EncOffset_RBV', doc="Encoder Offset converted into actual position units.")
    enc_scale = Cpt(EpicsSignal, ':PLC:AxisPar:EncScaling_RBV', doc="Encoder scaling numerator / denominator in EU/COUNT.")
    pos_lag_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:PosLagEn_RBV', doc="Enable/Disable state of Position Lag Monitor.")
    max_plc_limit_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMaxEn_RBV', doc="Enable/Disable state of controller static maximum limit")
    min_plc_limit_enabled = Cpt(EpicsSignal, ':PLC:AxisPar:SLimMinEn_RBV', doc="Enable/Disable state of controller static minimum limit")

def addEqualComparison(file: ConfigurationFile, config_name, axis_name, pv,
                       value, name="", description="", overwrite=False):
    """Given an ATEF ConfiurationFile, find the specified PVConfiguration,
    create and insert a new Equal comparison into the PVConfiguration.

    Args:
        file (String): The atef config file.
        config_name (String): The configuration to looks for.
        axis_name (String): The axis to add the comparison to. 
        pv (String): The PV name used to conduct the comparison. 
        value (Any): The value to compare to.
    """
    foundConfig = False
    if config_name not in [cfg.name for cfg in file.root.configs]:
        # no matching ConfigurationGroup
        return

    for config in file.root.configs:
        if config.name == config_name:
            foundConfig = True
            if axis_name not in [cfg.name for cfg in config.configs]:
                # no PV Configuration, need to create one
                config.configs.append(PVConfiguration(name=axis_name))
            for axis in config.configs:
                if axis.name == axis_name:
                    by_pv = axis.by_pv
                    new_comp = Equals(name=name, description=description, value=value)
                    if pv in by_pv and overwrite:
                        by_pv[pv] = [new_comp]
                    elif pv not in by_pv:
                        by_pv[pv] = [new_comp]
                    break
        if foundConfig:
            break
    

def addCurrentAxisParameters(file: ConfigurationFile, mirror, base_pv_axis, axis, overwrite=False):
    """ Add a new PVConfiguration in the ConfigurationGroup with name `mirror` """
    hardstop_config = OpticsHard(base_pv_axis, name='')
    signals = hardstop_config.get_instantiated_signals()

    for signal in signals:
        name = signal[1].name[1:]
        description = getattr(OpticsHard, signal[1].name[1:]).doc
        value = getattr(hardstop_config, signal[1].name[1:]).get()
        pv = getattr(hardstop_config, signal[1].name[1:]).pvname

        addEqualComparison(file, mirror, axis, pv, value, name, description, overwrite)

# grab base config file
file = ConfigurationFile()
file.root.name = "RIX Beamline"

# add config group for each mirror
for mirror_name in ['SP1K1 MONO', 'MR1K1 BEND', 'MR2K2 FLAT', 'MR3K2 KBH']:
    file.root.configs.append(ConfigurationGroup(name=mirror_name))

addCurrentAxisParameters(file, "SP1K1 MONO", "SP1K1:MONO:MMS:G_PI", "G_PI", True) 
addCurrentAxisParameters(file, "SP1K1 MONO", "SP1K1:MONO:MMS:G_H", "G_H", True) 
addCurrentAxisParameters(file, "SP1K1 MONO", "SP1K1:MONO:MMS:M_PI", "M_PI", True) 
addCurrentAxisParameters(file, "SP1K1 MONO", "SP1K1:MONO:MMS:M_H", "M_H", True) 

addCurrentAxisParameters(file, "MR1K1 BEND", "MR1K1:BEND:MMS:XUP", "XUP", True) 
addCurrentAxisParameters(file, "MR1K1 BEND", "MR1K1:BEND:MMS:YUP", "YUP", True) 
addCurrentAxisParameters(file, "MR1K1 BEND", "MR1K1:BEND:MMS:PITCH", "Pitch", True) 

addCurrentAxisParameters(file, "MR2K2 FLAT", "MR2K2:FLAT:MMS:X", "X", True) 
addCurrentAxisParameters(file, "MR2K2 FLAT", "MR2K2:FLAT:MMS:Y", "Y", True) 
addCurrentAxisParameters(file, "MR2K2 FLAT", "MR2K2:FLAT:MMS:PITCH", "Pitch", True) 

addCurrentAxisParameters(file, "MR3K2 KBH", "MR3K2:KBH:MMS:X", "X", True) 
addCurrentAxisParameters(file, "MR3K2 KBH", "MR3K2:KBH:MMS:Y", "Y", True) 
addCurrentAxisParameters(file, "MR3K2 KBH", "MR3K2:KBH:MMS:PITCH", "Pitch", True) 

    
with open("scratch.json", "w") as fd:
    json.dump(apischema.serialize(ConfigurationFile, file), fd, indent=4)
