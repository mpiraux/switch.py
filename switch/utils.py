#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#


import os
from datetime import datetime, timedelta
from json import JSONEncoder, JSONDecoder

import yaml
import yamlordereddictloader

mode_to_name = {
    0: 'Automated schedule',
    1: 'Keep ON',
    2: 'Keep OFF',
    3: 'Always ON',
    4: 'Always OFF',
    5: 'Timer'
}

mode_to_html = {
    0: '<span class="label label-success">%s</span>' % mode_to_name[0],
    1: '<span class="label label-warning">%s</span>' % mode_to_name[1],
    2: '<span class="label label-warning">%s</span>' % mode_to_name[2],
    3: '<span class="label label-danger">%s</span>' % mode_to_name[3],
    4: '<span class="label label-danger">%s</span>' % mode_to_name[4],
    5: '<span class="label label-default">%s</span>' % mode_to_name[5]
}


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.mkdir(path)


def load_config_file(path):
    with open(path, 'r') as f:
        return yaml.load(f, Loader=yamlordereddictloader.Loader)


def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    http://flask.pocoo.org/snippets/33/
    """
    now = datetime.now()
    diff = now - dt

    periods = (
        (diff.days // 365, "year", "years"),
        (diff.days // 30, "month", "months"),
        (diff.days // 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds // 3600, "hour", "hours"),
        (diff.seconds // 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds")
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


class DateTimeDecoder(JSONDecoder):
    def __init__(self, *args, **kargs):
        JSONDecoder.__init__(self, object_hook=self.dict_to_object, *args, **kargs)

    @staticmethod
    def dict_to_object(d):
        if '__type__' not in d:
            return d

        t = d.pop('__type__')
        if t == 'datetime':
            return datetime(**d)
        else:
            d['__type__'] = t
            return d


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {
                '__type__': 'datetime',
                'year': obj.year,
                'month': obj.month,
                'day': obj.day,
                'hour': obj.hour,
                'minute': obj.minute,
                'second': obj.second,
                'microsecond': obj.microsecond,
            }
        else:
            return JSONEncoder.default(self, obj)
