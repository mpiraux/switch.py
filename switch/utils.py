import os
from datetime import datetime

import yaml

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
        return yaml.load(f)


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
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default
