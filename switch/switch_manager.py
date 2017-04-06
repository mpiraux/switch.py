import json
import os
from importlib import import_module

from switch import join_root
from switch.time.schedule import Schedule


class SwitchManager(object):
    """ A singleton class interfacing switches with the application. """

    def __init__(self, switch_definitions):
        self._switches = switch_definitions
        self._modules = {}
        self._schedules = {}
        self._states = {}
        for switch in switch_definitions:
            self._states[switch] = {'level': 0, 'mode': 0}
            self._modules[switch] = import_module('switch.switches.%s' % self._switches[switch]['module'])
            self._load_schedules(switch)

    def _load_schedules(self, switch_id):
        self._schedules[switch_id] = {}
        schedules_path = self._get_schedules_path(switch_id)
        if os.path.exists(schedules_path):
            with open(schedules_path, 'r') as f:
                for schedule_name, schedule_dict in json.load(f).items():
                    self._schedules[switch_id][schedule_name] = Schedule.from_dict(schedule_dict)

    def save_schedules(self, switch_id):
        schedules_path = self._get_schedules_path(switch_id)
        with open(schedules_path, 'w') as f:
            json.dump({schedule_name: schedule.to_dict() for schedule_name, schedule in self._schedules[switch_id].items()}, f)

    def __iter__(self):
        items = []
        for switch_id in self._switches:
            items.append(self[switch_id])
        return iter(items)

    def __getitem__(self, switch_id):
        attrs = self._switches[switch_id]
        switch_dict = {'id': switch_id, 'name': attrs['name'], 'schedules': self._schedules[switch_id]}
        switch_dict.update(self._states[switch_id])
        return switch_dict

    @staticmethod
    def _get_schedules_path(switch_id):
        return join_root(os.path.join('data', switch_id + os.extsep + 'json'))
