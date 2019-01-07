from . import db


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

