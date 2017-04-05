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
        if intervals is None:
            intervals = []
        self._intervals = intervals

    def add_interval(self, new_interval: WeightedTimeInterval):
        """ Adds the interval if it is not overlapping with any other interval, otherwise does nothing. """
        for idx, interval in enumerate(self._intervals):
            if new_interval < interval:
                self._intervals.insert(idx, new_interval)
            elif new_interval in interval:
                return
        self._intervals.append(new_interval)

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
                return interval.weight, previous_instant

    def get_next_action(self):
        """
            Returns a tuple (weight, datetime) where weight can be None (indicating the end of the current action)
            representing the next action of the schedule. If the schedule is empty returns None.
        """
        if not self._intervals:
            return None

        now = Instant.now_to_instant()
        for idx, interval in enumerate(self._intervals):
            if now in interval and interval.b < self._intervals[(idx + 1) % len(self._intervals)].a:
                # There is a gap between the current interval and the next one.
                return None, interval.b.to_datetime()
            if now < interval:
                return interval.weight, interval.a.to_datetime()
        # No interval was found, going back to the start and add one week.
        interval = self._intervals[0]
        return interval.weight, interval.a.to_datetime() + timedelta(weeks=1)

    def __repr__(self):
        return '%s(intervals=%s)' % (self.__class__.__qualname__, repr(self._intervals))
