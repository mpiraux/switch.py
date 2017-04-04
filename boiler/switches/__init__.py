"""
    This package contains user-defined modules for controlling the switches defined in the configuration file.
    A minimal module looks like::

        def on(level=0):
            pass

        def off():
            pass    
            
    Those functions will be called when the switch changes states and should effectively actuate it.
"""
