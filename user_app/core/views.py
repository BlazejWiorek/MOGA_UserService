from .. import db
from ..models import Population, PopulationMetrics, Front, Exemplar
from . import main, models_files
from .forms import AddPopulationForm, UploadForm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import AjaxDataSource
from flask import redirect, url_for, flash, render_template, request, jsonify, session, current_app, send_from_directory
from sqlalchemy import select, join, and_, desc
from user_app.models import Population, PopulationMetricsChoices, FrontMetrics

import numpy as np
import os
import pickle
import requests


@main.before_app_first_request
def remove_workers():

    workers_dict = dict()
    with open(current_app.config['WORKERS_FILE_PATH'], 'wb') as workers_file:
        pickle.dump(workers_dict, workers_file)
    db.drop_all()
    db.create_all()


@main.route('/add_population', methods=['GET', 'POST'])
def add_population():
    uploaded_model_files = get_uploaded_model_names(current_app.config['MODELS_DIRECTORY'])
    if not uploaded_model_files:
        flash('Before you add a population, you need to upload model file')
        return redirect(url_for('main.upload_model'), code=302)
    population_form = AddPopulationForm()
    population_form.model_file.choices = [(file, file) for i, file in enumerate(uploaded_model_files)]
    if population_form.validate_on_submit():
        if Population.query.filter_by(name=population_form.name.data).first() is None:
            population = Population(name=population_form.name.data,
                                    size=population_form.size.data,
                                    crossover=population_form.cross_coef.data,
                                    mutation=population_form.mut_coef.data,
                                    generations=population_form.max_generations.data,
                                    model_file=population_form.model_file.data)
            db.session.add(population)
            db.session.commit()
            flash('Population added')
        else:
            flash('Population name must be unique')
        return redirect(url_for('main.add_population'))
    return render_template('main/add_population.html', form=population_form)


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    messages = session.get('dashboard_message', [])
    for msg in messages:
        flash(msg)

    populations = Population.query.all()
    if len(populations) == 0:
        flash('Before you route to dashboard, you need to add population')
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
                           plotting_variant=plotting_variant,
                           population_name=population_name,
                           plots=plots)


@main.route('/worker_ready/<worker_id>/<worker_url>', methods=['POST'])
def register_worker(worker_id, worker_url):
    worker_url = 'http://' + worker_url
    add_worker(current_app.config['WORKERS_FILE_PATH'], worker_id, worker_url)
    return jsonify({})


@main.route('/init_evolution_task/<pop_id>', methods=['POST'])
def init_evolution(pop_id):
    available_worker_data = get_available_worker(current_app.config['WORKERS_FILE_PATH'])
    if not available_worker_data:
        return jsonify(no_workers=1)
    available_worker_url, available_worker_id = available_worker_data
    evolution_request_data = create_evolution_request_data(available_worker_id, pop_id)
    requests.post(available_worker_url, data=evolution_request_data)
    return jsonify(no_workers=0)


@main.route('/model/<path:model_file>', methods=['GET', 'POST'])
def get_model(model_file):
    if request.method == 'GET':
        models_dir = current_app.config['UPLOADED_TEXT_DEST']
        models = get_uploaded_model_names(models_dir)
        if model_file in models:
            return send_from_directory(directory=models_dir, filename=model_file, as_attachment=True)
    else:
        worker_id, model_file = pickle.loads(request.data)
        invalid_model(current_app.config['WORKERS_FILE_PATH'], worker_id, model_file)
    return jsonify({})


@main.route('/workers')
def workers():
    return render_template('main/workers.html')


@main.route('/workers_update', methods=['GET', 'POST'])
def workers_update():
    return jsonify(get_workers(current_app.config['WORKERS_FILE_PATH']))


@main.route('/task_finished/<worker_id>/<population_name>', methods=['POST'])
def task_finished(worker_id, population_name):
    worker_finished_task(current_app.config['WORKERS_FILE_PATH'], worker_id, population_name)
    return jsonify({})


def get_workers(workers_file_path):
    with open(workers_file_path, 'rb') as workers_file:
        workers_dict = pickle.load(workers_file)
    return workers_dict


def worker_finished_task(workers_file_path, worker_id, population_name):
    workers = get_workers(workers_file_path)
    worker = workers[worker_id]
    worker['notifications'] = 'Worker finished: ' + population_name
    worker['status'] = 'waiting'
    override_workers_file(workers_file_path, workers)


def add_worker(workers_file_path, worker_id, worker_url):
    workers_dict = dict()

    if os.path.getsize(workers_file_path) > 0:
        workers_dict = get_workers(workers_file_path)

    workers_dict[worker_id] = {'url': worker_url, 'status': 'waiting', 'notifications': None}
    override_workers_file(workers_file_path, workers_dict)


def create_evolution_request_data(worker_id, pop_id):
    query = select([Population.name, Population.model_file,
                    Population.generations, Population.size,
                    Population.mutation, Population.crossover]).\
        where(Population.population_id == pop_id)
    population = db.engine.execute(query).first()
    request_dict = {'worker_id': worker_id, **dict(population)}
    return pickle.dumps(request_dict)


def get_available_worker(workers_file_path):
    if os.path.getsize(workers_file_path) == 0:
        return None

    workers_dict = get_workers(workers_file_path)

    avail_workers = [(worker_id, workers_dict[worker_id]['url'])
                     for worker_id, worker_dict in workers_dict.items()
                     if worker_dict['status'] == 'waiting']

    if not avail_workers:
        return None

    avail_worker_id, avail_worker_url = avail_workers[0]
    workers_dict[avail_worker_id]['status'] = 'busy'
    override_workers_file(workers_file_path, workers_dict)
    return avail_worker_url, avail_worker_id


def override_workers_file(workers_file_path, new_workers_dict):
    with open(workers_file_path, 'wb') as workers_file:
        pickle.dump(new_workers_dict, workers_file)


def invalid_model(workers_file_path, worker_id, model_file):
    workers_dict = get_workers(workers_file_path)

    worker = workers_dict[worker_id]
    new_worker_dict = {'url': worker['url'], 'status': 'waiting', 'notifications': 'Model error: ' + model_file}
    del workers_dict[worker_id]
    override_workers_file(workers_file_path, {worker_id: new_worker_dict, **workers_dict})


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
        where(and_(Population.name == pop_name)). \
        order_by(desc(Front.generation))
    front = db.engine.execute(query).first()

    front_exemplars_query = select([Exemplar.length, Exemplar.profit]). \
        select_from(join(Front, Exemplar)). \
        where(Exemplar.front_id == front['front_id'])
    exemplars = db.engine.execute(front_exemplars_query).fetchall()

    exemplars_fitness = np.zeros((len(exemplars), 2))
    for i, exemplar in enumerate(exemplars):
        exemplars_fitness[i] = exemplar['length'], exemplar['profit']
    return exemplars_fitness


def get_metrics(pop_name):
    front_query = select([Front.front_id]).select_from(join(Population, Front)). \
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
            res.append(model_file)
    return res
