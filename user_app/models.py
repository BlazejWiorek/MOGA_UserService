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

    def __init__(self, **kwargs):
        super(Population, self).__init__(**kwargs)
        self.is_initialized = False

    def as_dict(self):
        pop_dict = {'name': self.name,
                    'size': self.size,
                    'crossover': self.crossover,
                    'mutation': self.mutation,
                    'generations': self.generations,
                    'model_file': 'model placeholder'}
        return pop_dict

    def as_table(self):
        table = PopulationTable([self.as_dict()])
        table.html_attrs = {'style': "width: 100%"}
        return table
