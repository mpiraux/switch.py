import json
import os

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_bower import Bower

from switch import join_root
from switch.switch_manager import SwitchManager
from switch.time.schedule import Schedule
from switch.time.time_interval import WeightedTimeInterval, Instant
from switch.utils import ensure_directory_exists, load_config_file
from switch.log import logger

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
        schedules = app.switch_manager[switch]['schedules']

        if 'replace-sched' in request.form and 'new-sched-name' in request.form:
            schedule_name = request.form['new-sched-name']
            app.switch_manager.delete_schedule(switch, request.form['replace-sched'])
            logger.info('Schedule %s will be replaced by %s', request.form['replace-sched'], schedule_name,
                        extra=dict(context=switch))
        else:
            schedule_name = request.form['name']

        schedule_intervals = json.loads(request.form['intervals'])
        if schedule_name in schedules:
            logger.info('A schedule with the name %s already exists for this switch', schedule_name, extra=dict(context=switch))
            flash('schedule_already_exists')
            return redirect(url_for('configure_switch', switch=switch))

        intervals = []
        for a, b, l in schedule_intervals:
            intervals.append(WeightedTimeInterval(Instant(minute=15 * a), Instant(minute=15 * b), w=l))
        app.switch_manager.add_schedule(switch, schedule_name, Schedule(intervals))
        logger.info('Schedule %s was created', schedule_name, extra=dict(context=switch))
        flash('schedule_created')
        return redirect(url_for('index'))


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
    app.switch_manager.delete_schedule(switch, schedule)
    logger.info('Schedule %s was deleted', extra=dict(context=switch))
    flash('schedule_deleted')
    return redirect(url_for('index'))


@app.route('/switch/<switch>/use/<schedule>', methods=['POST'])
def use_switch_schedule(switch, schedule):
    app.switch_manager.use_schedule(switch, schedule)
    logger.info('Schedule %s is active', extra=dict(context=switch))
    flash('schedule_used')
    return redirect(url_for('index'))


@app.route('/switch/<switch>/mode/<int:mode>', methods=['POST'])
@app.route('/switch/<switch>/mode/<int:mode>/level/<int:level>', methods=['POST'])
def switch_mode(switch, mode, level=1):
    level = 0 if mode == 2 or mode == 4 else level
    app.switch_manager.switch_mode(switch, mode, level=level)
    logger.info('New settings {mode=%d, level=%d}', mode, level, extra=dict(context=switch))
    flash('mode_switched')
    return redirect(url_for('index'))


if __name__ == '__main__':
    logger.debug('Starting the app', extra=dict(context='General'))
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
