from boiler.time.time_interval import WeightedTimeInterval, Instant


class Planning(object):
    """
        A class representing a set of non overlapping weighted time interval spanning over a week.
        
        >>> i1 = WeightedTimeInterval(Instant(0, 1, 0), Instant(0, 2, 0), w=1)
        >>> i2 = WeightedTimeInterval(Instant(1, 1, 0), Instant(1, 2, 0), w=2)
        >>> p = Planning()
        >>> p.add_interval(i1)
        >>> p.add_interval(i2)
        >>> repr(p) == repr(Planning(intervals=[i1, i2]))
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

    def __repr__(self):
        return '%s(intervals=%s)' % (self.__class__.__qualname__, repr(self._intervals))
