#
# This file is part of switch.py. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#
import hashlib
import json
import os

from flask import Flask, render_template, request, flash, redirect, url_for, Response
from flask_bower import Bower

from switch import join_root
from switch.switch_manager import SwitchManager
from switch.time.schedule import Schedule
from switch.time.time_interval import WeightedTimeInterval, Instant
from switch.utils import ensure_directory_exists, load_config_file, mode_to_html
from switch.log import app_logger as logger, frontend_logger, frontend_handler

ensure_directory_exists(join_root('data'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['BOWER_COMPONENTS_ROOT'] = '../bower_components'
app.config['BOWER_QUERYSTRING_REVVING'] = False
Bower(app)
app.switch_config = load_config_file(join_root('configuration' + os.extsep + 'yaml'))
app.switch_manager = SwitchManager(app.switch_config['switches'])
frontend_handler.get_context_name = lambda x: app.switch_manager[x]['name'] if x in app.switch_manager else x.title()


def check_auth(user, password):
    return user == app.switch_config['user'] and hashlib.sha256(password.encode()).hexdigest() == app.switch_config['password']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.before_request
def ensure_auth():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()


@app.context_processor
def inject_switch_manager():
    return dict(switch_manager=app.switch_manager)


@app.route('/')
def index():
    return render_template('index.html', logs=frontend_handler.get_records())


@app.route('/configuration/<switch>', methods=['GET', 'POST'])
def configure_switch(switch):
    def get():
        return render_template('configuration.html', switch=app.switch_manager[switch], schedule=None)

    def post():
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

    return get() if request.method == 'GET' else post()


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
    logger.info('Schedule %s is active', schedule, extra=dict(context=switch))
    frontend_logger.info('Schedule %s was set as active', schedule, extra=dict(context=switch))
    flash('schedule_used')
    return redirect(url_for('index'))


@app.route('/switch/<switch>/mode/<int:mode>', methods=['POST'])
@app.route('/switch/<switch>/mode/<int:mode>/level/<int:level>', methods=['POST'])
def switch_mode(switch, mode, level=1):
    level = 0 if mode == 2 or mode == 4 else level
    app.switch_manager.switch_mode(switch, mode, level=level)
    logger.info('New settings {mode=%d, level=%d}', mode, level, extra=dict(context=switch))
    if app.switch_manager[switch]['levels'] > 1 and mode not in [0, 2, 4]:
        frontend_logger.info('Switch was set to <small>%s</small> at level %d by IP %s', mode_to_html[mode], level,
                             request.remote_addr, extra=dict(context=switch))
    else:
        frontend_logger.info('Switch was set to <small>%s</small> by IP %s', mode_to_html[mode], request.remote_addr,
                             extra=dict(context=switch))
    flash('mode_switched')
    return redirect(url_for('index'))


if __name__ == '__main__':
    logger.debug('Starting the app', extra=dict(context='General'))
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
