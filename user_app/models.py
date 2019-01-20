from . import db
from flask_table import Table, Col


class PopulationTable(Table):

    def sort_url(self, col_id, reverse=False):
        pass

    size = Col('Population size')
    crossover = Col('Crossover')
    mutation = Col('Mutation')
    generations = Col('Generations')
    model_file = Col('Model File')


class Population(db.Model):
    __tablename__ = 'Population'
    population_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    # hyperparams
    size = db.Column(db.Integer)
    crossover = db.Column(db.Float)
    mutation = db.Column(db.Float)

    # execution params
    generations = db.Column(db.Integer)
    model_file = db.Column(db.String(150))

    pop_metrics = db.relationship("PopulationMetrics", back_populates="population")
    fronts = db.relationship("Front", back_populates="population")


    def __init__(self, model_file=None, **kwargs):
        super(Population, self).__init__(**kwargs)
        self.is_initialized = False
        self.model_file = model_file

    def as_dict(self):
        pop_dict = {'name': self.name,
                    'size': self.size,
                    'crossover': self.crossover,
                    'mutation': self.mutation,
                    'generations': self.generations,
                    'model_file': self.model_file}
        return pop_dict

    def as_table(self):
        table = PopulationTable([self.as_dict()])
        table.html_attrs = {'style': "width: 100%"}
        return table


class PopulationMetrics(db.Model):
    __tablename__ = 'PopulationMetrics'

    pop_matric_id = db.Column(db.Integer, primary_key=True)
    generation = db.Column(db.Integer)

    routes_variety = db.Column(db.Float)
    plans_variety = db.Column(db.Float)

    min_length = db.Column(db.Float)
    avg_length = db.Column(db.Float)
    max_length = db.Column(db.Float)
    std_length = db.Column(db.Float)

    min_profit = db.Column(db.Float)
    avg_profit = db.Column(db.Float)
    max_profit = db.Column(db.Float)
    std_profit = db.Column(db.Float)

    avg_exec_time = db.Column(db.Integer)

    population_id = db.Column(db.Integer, db.ForeignKey('Population.population_id'))
    population = db.relationship("Population", back_populates="pop_metrics")


class Front(db.Model):
    __tablename__ = 'Front'
    front_id = db.Column(db.Integer, primary_key=True)
    generation = db.Column(db.Integer)

    population_id = db.Column(db.Integer, db.ForeignKey('Population.population_id'))
    population = db.relationship("Population", back_populates="fronts")

    exemplars = db.relationship("Exemplar", back_populates="front")
    metrics = db.relationship("FrontMetrics", back_populates="front")


class Exemplar(db.Model):
    __tablename__ = 'Exemplar'
    exemplar_id = db.Column(db.Integer, primary_key=True)
    profit = db.Column(db.Float)
    length = db.Column(db.Float)
    repr = db.Column(db.Text)

    front_id = db.Column(db.Integer, db.ForeignKey('Front.front_id'))
    front = db.relationship("Front", back_populates="exemplars")


class FrontMetrics(db.Model):
    __tablename__ = 'FrontMetrics'
    front_metrics_id = db.Column(db.Integer, primary_key=True)
    cardinality = db.Column(db.Integer)
    os = db.Column(db.Float)
    sp = db.Column(db.Float)
    sp_field = db.Column(db.Float)
    hypervolume = db.Column(db.Float)
    angle = db.Column(db.Float)
    sp_angle = db.Column(db.Float)
    euclidean = db.Column(db.Float)

    front_id = db.Column(db.Integer, db.ForeignKey('Front.front_id'))
    front = db.relationship("Front", back_populates="metrics")


class PopulationMetricsChoices:
    MAX_LENGTH = 'Max length'
    AVG_LENGTH = 'Average length'
    MIN_LENGTH = 'Min length'
    MAX_PROFIT = 'Max length'
    AVG_PROFIT = 'Average length'
    MIN_PROFIT = 'Mix length'
    STD_PROFIT = 'Standard deviation of profit'
    STD_LENGTH = 'Standard deviation of length'
    VARIETY = 'Variety per generation'

    MAPPER = {MAX_LENGTH: 'max_length',
              AVG_LENGTH: 'avg_length',
              MIN_LENGTH: 'min_length',
              MAX_PROFIT: 'max_profit',
              AVG_PROFIT: 'avg_profit',
              MIN_PROFIT: 'min_profit',
              STD_PROFIT: 'std_profit',
              STD_LENGTH: 'std_length',
              VARIETY: 'routes_variety'}

    @staticmethod
    def to_list():
        return [PopulationMetricsChoices.MAX_LENGTH, PopulationMetricsChoices.AVG_LENGTH,
                PopulationMetricsChoices.MIN_LENGTH, PopulationMetricsChoices.MAX_PROFIT,
                PopulationMetricsChoices.AVG_PROFIT, PopulationMetricsChoices.MIN_PROFIT,
                PopulationMetricsChoices.STD_PROFIT, PopulationMetricsChoices.STD_LENGTH,
                PopulationMetricsChoices.VARIETY]

    @staticmethod
    def to_column(selection):
        return PopulationMetricsChoices.MAPPER.get(selection, 'avg_profit')