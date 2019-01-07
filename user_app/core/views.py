from . import main
from flask import redirect, url_for


@main.route('/add_population')
def add_population():
    return 'Add population'


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    if True:
        return redirect(url_for('main.add_population'))
    return 'Placeholder'