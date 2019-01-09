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


class PopulationMetricsChoices:
    MAX_LENGTH = 'Max length'
    AVG_LENGTH = 'Average length'
    MIN_LENGTH = 'Min length'
    MAX_PROFIT = 'Max length'
    AVG_PROFIT = 'Average length'
    MIN_PROFIT = 'Mix length'
    MIN_MAX_AVG = 'Min - Max - Avg'
    STD_PROFIT = 'Standard deviation of profit'
    STD_LENGTH = 'Standard deviation of length'
    VARIETY = 'Variety per generation'

    @staticmethod
    def to_list():
        return [PopulationMetricsChoices.MAX_LENGTH, PopulationMetricsChoices.AVG_LENGTH,
                PopulationMetricsChoices.MIN_LENGTH, PopulationMetricsChoices.MAX_PROFIT,
                PopulationMetricsChoices.AVG_PROFIT, PopulationMetricsChoices.MIN_PROFIT,
                PopulationMetricsChoices.MIN_MAX_AVG, PopulationMetricsChoices.STD_PROFIT,
                PopulationMetricsChoices.STD_LENGTH, PopulationMetricsChoices.VARIETY]