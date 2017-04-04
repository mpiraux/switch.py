from flask import Flask, render_template
from flask_bower import Bower

app = Flask(__name__)
app.config['BOWER_COMPONENTS_ROOT'] = '../bower_components'
app.config['BOWER_QUERYSTRING_REVVING'] = False


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    Bower(app)
    app.run()
