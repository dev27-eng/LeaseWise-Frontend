from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired, Email

class TermsAcceptanceForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    accept_terms = BooleanField('I accept the Terms of Service', 
                               validators=[DataRequired(message='You must accept the terms to continue')])
