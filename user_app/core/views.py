from .. import db
from ..models import Population, PopulationMetrics, Front, Exemplar
from . import main, models_files
from .forms import AddPopulationForm, UploadForm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import AjaxDataSource
from flask import redirect, url_for, flash, render_template, request, jsonify, session
from sqlalchemy import select, join, and_, desc
from user_app.models import Population, PopulationMetricsChoices, FrontMetrics

import numpy as np
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


@main.route('/population_metrics/<population_name>/<plotting_variant>', methods=['GET', 'POST'])
def population_metrics(population_name, plotting_variant):
    population_metrics = get_population_metrics(population_name, PopulationMetricsChoices.to_column(plotting_variant))
    return jsonify(x=population_metrics[:, 1].tolist(), y=population_metrics[:, 0].tolist())


@main.route('/front_data/<population_name>', methods=['GET', 'POST'])
def front_data(population_name):
    front_data = get_front_data(population_name)
    return jsonify(x=front_data[:, 1].tolist(), y=front_data[:, 0].tolist())


@main.route('/front_metrics/<population_name>', methods=['GET', 'POST'])
def front_metrics_data(population_name):
    if request.method == 'POST':
        return jsonify({})
    metrics = get_metrics(population_name)
    return jsonify(metrics)


@main.route('/dashboard/<population_name>/<plotting_variant>', methods=['GET', 'POST'])
def population_details(population_name, plotting_variant):
    if request.method == 'POST':
        req_form = request.form
        plotting_variant = req_form['plotting_variant']
        return redirect(url_for('main.population_details',
                                plotting_variant=plotting_variant,
                                population_name=population_name))

    plots = []
    plots.append(create_population_metrics_plot(
        request.url_root + 'population_metrics/' + population_name + '/' + plotting_variant))

    plots.append(create_front_plot(request.url_root + 'front_data/' + population_name))

    return render_template('main/population_details.html',
                           feature_names=PopulationMetricsChoices.to_list(),
                           plotting_variant='default',
                           population_name=population_name,
                           plots=plots)


@main.route('/worker_ready/<worker_id>', methods=['POST'])
def register_worker(worker_id):
    active_workers = session.get('active_workers', [])
    active_workers.append(worker_id)
    session['active_workers'] = active_workers
    return jsonify({})


def get_population_metrics(pop_name, selected_feature):
    query = select([Population.name, PopulationMetrics]). \
                    select_from(join(Population, PopulationMetrics)). \
                    where(and_(Population.name == pop_name))
    query_res = db.engine.execute(query).fetchall()
    metric_values = np.zeros((len(query_res), 2))
    for i, res in enumerate(query_res):
        metric_values[i, 0] = res[selected_feature]
        metric_values[i, 1] = res['generation']
    return metric_values


def get_front_data(pop_name):
    query = select([Population.name, Front.generation, Front.front_id]). \
                    select_from(join(Population, Front)). \
                    where(and_(Population.name == pop_name)).\
                    order_by(desc(Front.generation))
    front = db.engine.execute(query).first()

    front_exemplars_query = select([Exemplar.length, Exemplar.profit]).\
        select_from(join(Front, Exemplar)).\
        where(Exemplar.front_id == front['front_id'])
    exemplars = db.engine.execute(front_exemplars_query).fetchall()

    exemplars_fitness = np.zeros((len(exemplars), 2))
    for i, exemplar in enumerate(exemplars):
        exemplars_fitness[i] = exemplar['length'], exemplar['profit']
    return exemplars_fitness


def get_metrics(pop_name):
    front_query = select([Front.front_id]).select_from(join(Population, Front)).\
        where(Population.name == pop_name).order_by(desc(Front.generation))
    front_id = db.engine.execute(front_query).first()['front_id']

    front_metrics_query = select([FrontMetrics]).where(FrontMetrics.front_id == front_id)
    front_metrics = db.engine.execute(front_metrics_query).first()
    front_m = dict(front_metrics)
    return front_m


def create_population_metrics_plot(url):
    source = AjaxDataSource(data_url=url,
                            polling_interval=10000)
    source.data = dict(x=[], y=[])
    plot = figure(plot_width=700, plot_height=350)
    plot.line('x', 'y', source=source, line_width=4)
    script, div = components(plot)
    return script, div


def create_front_plot(url):
    source = AjaxDataSource(data_url=url,
                            polling_interval=10000)
    source.data = dict(x=[], y=[])
    plot = figure(plot_width=700, plot_height=350)
    plot.circle('x', 'y', source=source, line_width=4)
    script, div = components(plot)
    return script, div


def get_uploaded_model_names(dir: str):
    res = []
    for model_file in os.listdir(dir):
        model_file_path = os.path.join(dir, model_file)
        if os.path.isfile(model_file_path):
            res.append((model_file_path, model_file))
    return res