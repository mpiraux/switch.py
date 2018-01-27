#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#


import json
import os
import sched
from importlib import import_module
from threading import Thread

import time

from switch import join_root
from switch.time.schedule import Schedule
from switch.log import app_logger as logger


class SwitchManager(object):
    """ A singleton class interfacing switches with the application. """

    def __init__(self, switch_definitions):
        self._switches = switch_definitions
        self._modules = {}
        self._schedules = {}
        self._states = {}
        logger.debug('Proceeding to load switches', extra=dict(context='General'))
        for switch in switch_definitions:
            self._states[switch] = {'level': 0, 'mode': 0}
            self._modules[switch] = import_module('switch.switches.%s' % self._switches[switch]['module'])
            self._load_switch(switch)
            logger.debug('\nstate: %s\nschedules: %s', self._states[switch], self._schedules[switch], extra=dict(context=switch))
        logger.debug('Proceeding to start scheduler', extra=dict(context='General'))
        self._running = True
        self._next_event = None
        self._sched = sched.scheduler(timefunc=time.time)
        self._sched_thread = Thread(target=self._run_sched)
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
                self.set_level(switch_id, self._states[switch_id]['level'])

    def save_switch(self, switch_id):
        switch_data_path = self._get_switch_data_path(switch_id)
        with open(switch_data_path, 'w') as f:
            switch_data = dict(**self._states[switch_id])
            switch_data['schedules'] = {schedule_name: schedule.to_dict()
                                        for schedule_name, schedule in self._schedules[switch_id].items()}
            json.dump(switch_data, f)

    def add_schedule(self, switch, schedule_name, schedule):
        self._schedules[switch][schedule_name] = schedule
        self.save_switch(switch)

    def delete_schedule(self, switch, schedule_name):
        self._schedules[switch].pop(schedule_name)
        if schedule_name == self._states[switch].get('active_schedule'):
            self._cancel_events()
            self._states[switch].pop('active_schedule')
        self.save_switch(switch)
        self._schedule_next_event()

    def use_schedule(self, switch, schedule_name):
        if schedule_name in self._schedules[switch]:
            self._cancel_events()
            self._states[switch]['active_schedule'] = schedule_name
            current_level, _ = self._schedules[switch][schedule_name].get_current_action()
            self.set_level(switch, current_level or 0)
            self._schedule_next_event()

    def switch_mode(self, switch, mode, level):
        self._states[switch]['mode'] = mode
        if mode == 0:
            self.use_schedule(switch, self._states[switch].get('active_schedule'))
        else:
            self._cancel_events()
            self.set_level(switch, level)

    def set_level(self, switch, level):
        self._states[switch]['level'] = level
        if level > 0:
            self._modules[switch].on(switch, level)
        else:
            self._modules[switch].off(switch)
        self.save_switch(switch)
        logger.info('New level=%d', level, extra=dict(context=switch))

    def __iter__(self):
        return iter([self[switch_id] for switch_id in self._switches])

    def __getitem__(self, switch_id):
        attrs = self._switches.get(switch_id)
        if not attrs:
            return None
        switch_dict = {'id': switch_id, 'name': attrs['name'], 'levels': attrs['levels'],
                       'schedules': self._schedules[switch_id]}
        switch_dict.update(self._states[switch_id])
        active_schedule = switch_dict.get('active_schedule')
        if active_schedule:
            next_action = self._schedules[switch_id][active_schedule].get_next_action()
            if next_action:
                level, date = next_action
                switch_dict['next_action'] = (level or 0, date)
        return switch_dict

    def __contains__(self, item):
        return self[item] is not None

    def __del__(self):
        self._running = False
        self._cancel_events()

    def determine_next_actions(self):
        actions = [self.determine_next_action_for(switch) for switch in self._states]
        actions = filter(lambda x: x is not None, actions)

        earliest_actions = []
        instant = None
        for action in actions:
            switch, weight, datetime = action
            if not earliest_actions:
                earliest_actions.append((switch, weight, datetime))
                instant = datetime
            elif datetime < instant:
                earliest_actions = [(switch, weight, datetime)]
                instant = datetime
            elif datetime == instant:
                earliest_actions.append((switch, weight, datetime))

        return earliest_actions, instant

    def determine_next_action_for(self, switch):
        state = self._states[switch]
        schedule = self._schedules[switch].get(state.get('active_schedule'))
        if state['mode'] < 3 and schedule and schedule.get_next_action():
            weight, datetime = schedule.get_next_action()
            return switch, weight or 0, datetime
        else:
            # TODO: Handle timer
            pass
        return None

    def _cancel_events(self):
        if self._sched.queue:
            map(self._sched.cancel, self._sched.queue)

    def _schedule_next_event(self):
        self._cancel_events()
        actions, datetime = self.determine_next_actions()
        if actions:
            self._next_event = self._sched.enterabs(datetime.timestamp(), 1, self._handle_event, argument=(actions,))
            logger.info('Next scheduled event is %s and will affect switches %s', datetime,
                        [switch for switch, _, _ in actions], extra=dict(context='General'))

    def _handle_event(self, actions):
        logger.debug('A scheduled event expired', extra=dict(context='General'))
        for switch, level, _ in actions:
            state = self._states[switch]
            if state['mode'] < 3:
                self.switch_mode(switch, 0, level)
        self._schedule_next_event()

    def _run_sched(self):
        while self._running:
            self._sched.run()
            time.sleep(5)

    @staticmethod
    def _get_switch_data_path(switch_id):
        return join_root(os.path.join('data', switch_id + os.extsep + 'json'))
