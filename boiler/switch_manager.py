from importlib import import_module


class SwitchManager(object):
    """ A singleton class interfacing switches with the application. """
    def __init__(self, switch_definitions):
        self._switches = switch_definitions
        self._modules = {}
        self._plannings = {}
        self._states = {}
        for switch in switch_definitions:
            self._states[switch] = {'level': 0, 'mode': 0}
            self._modules[switch] = import_module('boiler.switches.%s' % self._switches[switch]['module'])

    def __iter__(self):
        items = []
        for switch_id, attrs in self._switches.items():
            switch_dict = {'id': switch_id, 'name': attrs['name']}
            switch_dict.update(self._states)
            items.append(switch_dict)
        return iter(items)
