from .. import db
from . import main, models_files
from .forms import AddPopulationForm, UploadForm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import AjaxDataSource
from flask import redirect, url_for, flash, render_template, request, jsonify
from user_app.models import Population, PopulationMetricsChoices


import os


@main.route('/add_population', methods=['GET', 'POST'])
def add_population():
    uploaded_model_files = get_uploaded_model_names(os.path.join(os.getcwd(), 'user_app/static/models'))
    if not uploaded_model_files:
        flash('Zanim dodasz populacje musisz dodać model')
        return redirect(url_for('main.upload_model'), code=302)
    population_form = AddPopulationForm()
    population_form.model_file.choices = uploaded_model_files
    if population_form.validate_on_submit():
        if Population.query.filter_by(name=population_form.name.data).first() is None:
            population = Population(name=population_form.name.data,
                                    size=population_form.size.data,
                                    crossover=population_form.cross_coef.data,
                                    mutation=population_form.mut_coef.data,
                                    generations=population_form.max_generations.data,
                                    model_file=population_form.model_file)
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
        flash('Zanim przejdziesz do panelu podglądu populacji musisz dodać populacje')
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


@main.route('/status/<population_name>', methods=['GET', 'POST'])
def generation_status(population_name):
    return jsonify(x=[1, 2, 3], y=[1, 2, 3])


@main.route('/dashboard/<population_name>/<plotting_variant>', methods=['GET', 'POST'])
def population_details(population_name, plotting_variant):
    if request.method == 'POST':
        req_form = request.form
        plotting_variant = req_form['plotting_variant']
        return redirect(url_for('main.population_details',
                                plotting_variant=plotting_variant,
                                population_name=population_name))
    plots = []
    plots.append(make_plot(population_name, plotting_variant))
    return render_template('main/population_details.html',
                           feature_names=PopulationMetricsChoices.to_list(),
                           plotting_variant='default',
                           population_name=population_name,
                           plots=plots)


def make_plot(population_name, plotting_variant):
    source = AjaxDataSource(data_url=request.url_root + 'status/' + population_name,
                            polling_interval=2100)
    print(request.url_root + 'status/' + population_name)
    source.data = dict(x=[], y=[])
    plot = figure(plot_height=300, sizing_mode='scale_width')
    plot.line('x', 'y', source=source, line_width=4)
    script, div = components(plot)
    return script, div


def get_uploaded_model_names(dir: str):
    res = []
    for model_file in os.listdir(dir):
        model_file_path = os.path.join(dir, model_file)
        if os.path.isfile(model_file_path):
            res.append((model_file_path, model_file))
    return res