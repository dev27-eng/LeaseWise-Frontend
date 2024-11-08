from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms.validators import DataRequired

class TermsAcceptanceForm(FlaskForm):
    accept_terms = BooleanField('I accept the Terms of Service', 
                               validators=[DataRequired(message='You must accept the terms to continue')])
