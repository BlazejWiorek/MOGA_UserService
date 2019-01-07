from .. import db
from . import main
from .forms import AddPopulationForm
from flask import redirect, url_for, flash, render_template
from user_app.models import Population


@main.route('/add_population', methods=['GET', 'POST'])
def add_population():
    population_form = AddPopulationForm()
    if population_form.validate_on_submit():
        if Population.query.filter_by(name=population_form.name.data).first() is None:
            population = Population(name=population_form.name.data,
                                    size=population_form.size.data,
                                    crossover=population_form.cross_coef.data,
                                    mutation=population_form.mut_coef.data,
                                    generations=population_form.max_generations.data,
                                    model_file='')
            db.session.add(population)
            db.session.commit()
            flash('Population added')
        else:
            flash('Population name must be unique')
        return redirect(url_for('main.add_population'))
    return render_template('main/add_population.html', form=population_form)


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    if True:
        return redirect(url_for('main.add_population'), code=302)
    return 'Placeholder'