import os

from flask import Flask, render_template
from flask_bower import Bower

from switch import join_root
from switch.switch_manager import SwitchManager
from switch.utils import ensure_directory_exists, load_config_file

ensure_directory_exists(join_root('data'))

app = Flask(__name__)
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


if __name__ == '__main__':
    app.run()
