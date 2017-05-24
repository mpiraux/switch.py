import json
import os
import sched
from importlib import import_module
from threading import Thread

import time

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
            self._load_switch(switch)
        self._running = True
        self._next_event = None
        self._sched = sched.scheduler(timefunc=time.time)
        self._sched_thread = Thread(target=self._run_sched)
        self._sched_thread.daemon = True
        self._schedule_next_event()
        self._sched_thread.start()

    def _load_switch(self, switch_id):
        self._schedules[switch_id] = {}
        switch_data_path = self._get_switch_data_path(switch_id)
        if os.path.exists(switch_data_path):
            with open(switch_data_path, 'r') as f:
                switch_data = json.load(f)
                schedules_data = switch_data.pop('schedules')
                self._states[switch_id] = switch_data
                for schedule_name, schedule_dict in schedules_data.items():
                    self._schedules[switch_id][schedule_name] = Schedule.from_dict(schedule_dict)

    def save_switch(self, switch_id):
        switch_data_path = self._get_switch_data_path(switch_id)
        with open(switch_data_path, 'w') as f:
            switch_data = dict(**self._states[switch_id])
            switch_data['schedules'] = {schedule_name: schedule.to_dict() for schedule_name, schedule in
                                        self._schedules[switch_id].items()}
            json.dump(switch_data, f)

    def add_schedule(self, switch, schedule_name, schedule):
        self._schedules[switch][schedule_name] = schedule
        self.save_switch(switch)

    def delete_schedule(self, switch, schedule_name):
        self._schedules[switch].pop(schedule_name)
        if schedule_name == self._states[switch].get('active_schedule'):
            self._states[switch].pop('active_schedule')
        self.save_switch(switch)
        self._schedule_next_event()

    def use_schedule(self, switch, schedule_name):
        if schedule_name in self._schedules[switch]:
            self._states[switch]['active_schedule'] = schedule_name
        self.save_switch(switch)
        self._schedule_next_event()

    def switch_mode(self, switch, mode, level, schedule_next=True):
        self._states[switch]['mode'] = mode
        self._states[switch]['level'] = level
        if level > 0:
            self._modules[switch].on(switch, level)
        else:
            self._modules[switch].off(switch, level)
        self.save_switch(switch)
        if schedule_next:
            self._schedule_next_event()

    def __iter__(self):
        return iter([self[switch_id] for switch_id in self._switches])

    def __getitem__(self, switch_id):
        attrs = self._switches[switch_id]
        switch_dict = {'id': switch_id, 'name': attrs['name'], 'levels': attrs['levels'],
                       'schedules': self._schedules[switch_id]}
        switch_dict.update(self._states[switch_id])
        return switch_dict

    def __del__(self):
        self._running = False
        map(self._sched.cancel, self._sched.queue)

    def determine_next_actions(self):
        actions = []
        for switch in self._states:
            state = self._states[switch]
            schedule = self._schedules[switch].get(state.get('active_schedule'))
            if state['mode'] < 3 and schedule:
                weight, datetime = schedule.get_next_action()
                weight = weight or 0
                if not actions:
                    actions.append((switch, weight, datetime))
                elif datetime < actions[0][2]:  # Action is closer than everything previously encountered
                    actions = [(switch, weight, datetime)]
                elif datetime == actions[0][2]:
                    actions.append((switch, weight, datetime))
            else:
                # TODO: Handle timer
                pass
        return actions

    def _schedule_next_event(self):
        map(self._sched.cancel, self._sched.queue)
        actions = self.determine_next_actions()
        self._next_event = self._sched.enterabs(actions[0][2].timestamp(), 1, self._handle_event, argument=(self, actions))

    def _handle_event(self, actions):
        print('handle', actions)
        for switch, level, _ in actions:
            state = self._states[switch]
            if state['mode'] < 3:
                self.switch_mode(switch, state['mode'], level, schedule_next=False)
        self._schedule_next_event()

    def _run_sched(self):
        while self._running:
            self._sched.run()
            time.sleep(5)

    @staticmethod
    def _get_switch_data_path(switch_id):
        return join_root(os.path.join('data', switch_id + os.extsep + 'json'))
