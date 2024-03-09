from app.models import Country
from sqlalchemy import func
from wtforms.validators import ValidationError

def check_alpha_code_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    country = Country.query.filter(func.lower(Country.code)==field.data.lower()).first()
    if country:
        raise ValidationError('Alpha Code already exists')

def check_country_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    country = Country.query.filter(func.lower(Country.name)==field.data.lower()).first()
    if country:
        raise ValidationError('Country already exists')
