from .. import db
from . import main, models_files
from .forms import AddPopulationForm, UploadForm
from flask import redirect, url_for, flash, render_template, request
from user_app.models import Population


import os


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
    populations = Population.query.all()
    if len(populations) == 0:
        return redirect(url_for('main.add_population'), code=302)
    return render_template('main/dashboard.html', populations=populations)


@main.route('/upload', methods=['GET', 'POST'])
def upload_model():
    upload_form = UploadForm()
    if request.method == 'POST' and 'model_file' in request.files:
        if upload_form.validate_on_submit():
            models_files.save(request.files['model_file'])
            flash('model file added')
        else:
            flash('wrong file extension')
        return redirect(url_for('main.upload_model'))
    return render_template('main/add_model.html', upload_form=upload_form)


def get_uploaded_model_names(dir: str):
    res = []
    for model_file in os.listdir(dir):
        model_file_path = os.path.join(dir, model_file)
        if os.path.isfile(model_file_path):
            res.append(model_file)
    return res