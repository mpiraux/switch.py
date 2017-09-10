#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#


from datetime import timedelta

from switch.time.time_interval import WeightedTimeInterval, Instant


class Schedule(object):
    """
        A class representing a set of non overlapping weighted time interval spanning over a week.
        
        >>> i1 = WeightedTimeInterval(Instant(0, 1, 0), Instant(0, 2, 0), w=1)
        >>> i2 = WeightedTimeInterval(Instant(1, 1, 0), Instant(1, 2, 0), w=2)
        >>> p = Schedule()
        >>> p.add_interval(i1)
        >>> p.add_interval(i2)
        >>> repr(p) == repr(Schedule(intervals=[i1, i2]))
        True
        >>> p.get_weight(Instant(0, 1, 30))
        1
        >>> p.get_weight(Instant(1, 2, 30)) is None
        True
    """

    def __init__(self, intervals=None):
        self._intervals = []
        for i in intervals:
            self.add_interval(i)

    def add_interval(self, new_interval: WeightedTimeInterval):
        """
            Adds the interval if it is not overlapping with any other interval.
            If both overlapping intervals have the same weight they will be merged into one.
        """
        for idx, interval in enumerate(self._intervals):
            if new_interval < interval:
                self._intervals.insert(idx, new_interval)
            elif new_interval in interval:
                return
            elif not new_interval > interval and new_interval.weight == interval.weight:
                # They are overlapping because one is not included in the other, nor strictly before or after.
                self._intervals[idx] = WeightedTimeInterval(min(new_interval.a, interval.a),
                                                            max(new_interval.b, interval.b),
                                                            interval.weight)
                return
        self._intervals.append(new_interval)

    def empty(self):
        self._intervals = []

    def get_weight(self, i: Instant):
        """
            Returns the weight associated with the interval containing the given instant if one contains it,
            otherwise returns None
        """
        for interval in self._intervals:
            if i in interval:
                return interval.weight
        return None

    def get_current_action(self):
        """
            Returns a tuple (weight, datetime) where weight can be None (indicating the end of the previous action)
            representing the current action of the schedule. If the schedule is empty returns None.
        """
        if not self._intervals:
            return None

        now = Instant.now_to_instant()
        for idx, interval in enumerate(self._intervals):
            if now in interval:
                return interval.weight, interval.a.to_datetime()
            if now < interval:
                previous_idx = (idx - 1) % len(self._intervals)
                previous_instant = self._intervals[previous_idx].b.to_datetime()
                if previous_idx > idx:
                    previous_instant -= timedelta(weeks=1)
                return None, previous_instant

    def get_next_action(self):
        """
            Returns a tuple (weight, datetime) where weight can be None (indicating the end of the current action)
            representing the next action of the schedule. If the schedule is empty returns None.
        """
        if not self._intervals:
            return None

        now = Instant.now_to_instant()
        for idx, interval in enumerate(self._intervals):
            if now < interval:
                return interval.weight, interval.a.to_datetime()
            next_interval = self._intervals[(idx + 1) % len(self._intervals)]
            if interval == next_interval:
                next_interval = WeightedTimeInterval(interval.a + timedelta(weeks=1), interval.b + timedelta(weeks=1), interval.weight)
            if now in interval and interval.b < next_interval.a:
                # There is a gap between the current interval and the next one.
                return None, interval.b.to_datetime()

        return self._intervals[0].weight, self._intervals[0].b + timedelta(weeks=1)

    def __repr__(self):
        return '%s(intervals=%s)' % (self.__class__.__qualname__, repr(self._intervals))

    def to_dict(self):
        return {'intervals': [interval.to_dict() for interval in self._intervals]}

    @classmethod
    def from_dict(cls, d):
        return cls([WeightedTimeInterval.from_dict(i) for i in d['intervals']])

    def to_interface_list(self):
        arrays = [[] for _ in range(7)]
        for interval in self._intervals:
            if interval.a.days == interval.b.days:
                arrays[interval.a.days].append([interval.a.seconds // (60*15), interval.b.seconds // (60*15), interval.weight])
            else:
                arrays[interval.a.days].append([interval.a.seconds // (60 * 15), 96, interval.weight])
                for day in range(interval.a.days+1, min(interval.b.days+1, 7)):
                    if day == interval.b.days:
                        if interval.b.seconds > 0:
                            arrays[day].append([0, interval.b.seconds // (60*15), interval.weight])
                    else:
                        arrays[day].append([0, 96, interval.weight])
        return arrays
