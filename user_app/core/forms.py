from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, NumberRange


class AddPopulationForm(FlaskForm):
    name = StringField('Population name', validators=[Length(1, 50), DataRequired(), Regexp('[a-zA-Z]+')])
    size = IntegerField('Amount of individuals', validators=[DataRequired(), NumberRange(min=0)])
    cross_coef = FloatField('Crossover coefficient', validators=[DataRequired(), NumberRange(min=0, max=1)])
    mut_coef = FloatField('Mutation coefficient', validators=[DataRequired(), NumberRange(min=0, max=1)])
    max_generations = IntegerField('Amount of generations', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

    def validate_tournament_coef(self, field):
        if self.size.data > field.data:
            raise ValidationError('Tournament coefficient has to be smaller than population size')
