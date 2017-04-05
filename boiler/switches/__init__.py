"""
    This package contains user-defined modules for controlling the switches defined in the configuration file.
    A minimal module looks like::

        def on(switch_name, level=0):
            pass

        def off(switch_name):
            pass    
            
    Those functions will be called when the switch changes states and should effectively actuate it.
"""
