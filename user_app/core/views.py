from . import main
from .forms import AddPopulationForm
from flask import redirect, url_for, flash, render_template


@main.route('/add_population', methods=['GET', 'POST'])
def add_population():
    population_form = AddPopulationForm()
    if population_form.validate_on_submit():
        if True:
            flash('Population added')
        else:
            flash('Population name must be unique')
        return redirect(url_for('main.add_population'))
    return render_template('main/add_population.html', form=population_form)


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    if True:
        return redirect(url_for('main.add_population'))
    return 'Placeholder'