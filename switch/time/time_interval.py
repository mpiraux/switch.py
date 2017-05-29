#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#


from datetime import timedelta, date, datetime, time


class Instant(timedelta):
    """ 
        A class representing an instant in a week with minute precision.  
        Days are automatically clamped for better interpretability of the results.
        
        >>> Instant(day=8, hour=2, minute=1)
        Instant(day=1, hour=2, minute=1)
    """

    def __new__(cls, day=0, hour=0, minute=0):
        return super().__new__(cls, days=day % 8, hours=hour, minutes=minute)

    def __repr__(self):
        return '%s(day=%d, hour=%d, minute=%d)' % (
            self.__class__.__qualname__, self.days, self.seconds // (60 * 60), (self.seconds // 60) % 60
        )

    def __lt__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self < other.a
        if isinstance(other, Instant):
            return super().__lt__(other)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self <= other.a
        if isinstance(other, Instant):
            return super().__le__(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self > other.b
        if isinstance(other, Instant):
            return super().__gt__(other)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self >= other.b
        if isinstance(other, Instant):
            return super().__ge__(other)
        return NotImplemented

    def to_datetime(self):
        today = date.today()
        week_start = datetime.combine(today - timedelta(days=today.weekday()), time())
        return week_start + self

    def to_dict(self):
        return {'day': self.days, 'hour': self.seconds // (60 * 60), 'minute': (self.seconds // 60) % 60}

    @classmethod
    def now_to_instant(cls):
        today = date.today()
        week_start = datetime.combine(today - timedelta(days=today.weekday()), time())
        delta = datetime.now() - week_start
        return cls(day=delta.days, hour=delta.seconds // (60 * 60), minute=(delta.seconds // 60) % 60)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class RelativeTimeInterval(object):
    """
        A class representing a relative time interval [a, b] in a week, with a <= b.
        
        >>> RelativeTimeInterval(Instant(0, 1, 0), Instant(0, 2, 0)) \
            in RelativeTimeInterval(Instant(0, 0, 0), Instant(1, 0, 0))
        True
        
        >>> RelativeTimeInterval(Instant(1, 1, 0), Instant(3, 1, 0)) \
            in RelativeTimeInterval(Instant(1, 4, 0), Instant(1, 6, 0))
        False
        
        >>> Instant(0, 1, 30) in RelativeTimeInterval(Instant(0, 1, 0), Instant(0, 2, 0))
        True
        
        >>> Instant(1, 1, 30) in RelativeTimeInterval(Instant(2, 1, 0), Instant(3, 2, 0))
        False
    """

    def __init__(self, a: Instant, b: Instant):
        assert a <= b
        self.a = a
        self.b = b

    def __contains__(self, item):
        if isinstance(item, RelativeTimeInterval):
            return self.a <= item.a and self.b >= item.b
        if isinstance(item, Instant):
            return self.a <= item <= self.b
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self.b < other.a
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self.b <= other.a
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self.a > other.b
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, RelativeTimeInterval):
            return self.a >= other.b
        return NotImplemented

    def __repr__(self):
        return '%s(a=%s, b=%s)' % (self.__class__.__qualname__, repr(self.a), repr(self.b))


class WeightedTimeInterval(RelativeTimeInterval):
    """
        A class representing a relative time interval in a week associated with an integer weight.
        Also adds dict dumping and loading.
    """

    def __init__(self, a: Instant, b: Instant, w: int = 0):
        super().__init__(a, b)
        self.weight = w

    def __repr__(self):
        return '%s(a=%s, b=%s, w=%d)' % (self.__class__.__qualname__, repr(self.a), repr(self.b), self.weight)

    def to_dict(self):
        return {'a': self.a.to_dict(), 'b': self.b.to_dict(), 'w': self.weight}

    @classmethod
    def from_dict(cls, d):
        return cls(a=Instant.from_dict(d['a']), b=Instant.from_dict(d['b']), w=d['w'])

