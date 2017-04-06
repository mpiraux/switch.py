import json
import os

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_bower import Bower

from switch import join_root
from switch.switch_manager import SwitchManager
from switch.time.schedule import Schedule
from switch.time.time_interval import WeightedTimeInterval, Instant
from switch.utils import ensure_directory_exists, load_config_file

ensure_directory_exists(join_root('data'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['BOWER_COMPONENTS_ROOT'] = '../bower_components'
app.config['BOWER_QUERYSTRING_REVVING'] = False
Bower(app)
app.switch_config = load_config_file(join_root('configuration' + os.extsep + 'yaml'))
app.switch_manager = SwitchManager(app.switch_config['switches'])


@app.context_processor
def inject_switch_manager():
    return dict(switch_manager=app.switch_manager)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/configuration/<switch>', methods=['GET', 'POST'])
def configure_switch(switch):
    if request.method == 'GET':
        return render_template('configuration.html', switch=app.switch_manager[switch], schedule=None)
    elif request.method == 'POST':
        try:
            schedules = app.switch_manager[switch]['schedules']

            if 'replace-sched' in request.form and 'new-sched-name' in request.form:
                new_schedule_name = request.form['new-sched-name']
                schedules.pop(request.form['replace-sched'], None)
            else:
                new_schedule_name = request.form['name']

            new_schedule_intervals = json.loads(request.form['intervals'])
            if new_schedule_name in schedules:
                flash('schedule_already_exists')
                return redirect(url_for('configure_switch', switch=switch))

            intervals = []
            for a, b in new_schedule_intervals:
                intervals.append(WeightedTimeInterval(Instant(minute=15*a), Instant(minute=15*b), w=1))
            schedules[new_schedule_name] = Schedule(intervals)
            app.switch_manager.save_schedules(switch)
            flash('schedule_created')
            return redirect(url_for('index'))
        except KeyError as e:
            print(e)


@app.route('/configuration/<switch>/<schedule>')
def configure_switch_schedule(switch, schedule):
    return render_template(
        'configuration.html',
        switch=app.switch_manager[switch],
        schedule_name=schedule,
        schedule=app.switch_manager[switch]['schedules'].get(schedule)
    )


@app.route('/configuration/<switch>/<schedule>/delete', methods=['POST'])
def delete_switch_schedule(switch, schedule):
    app.switch_manager[switch]['schedules'].pop(schedule)
    app.switch_manager.save_schedules(switch)
    flash('schedule_deleted')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()