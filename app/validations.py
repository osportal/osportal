from app.models import Company, Country, Entt, Site
from sqlalchemy import func
from wtforms.validators import ValidationError


def check_entt_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    entt = Entt.query.filter(func.lower(Entt.name)==field.data.lower()).first()
    if entt:
        raise ValidationError('Entitlement Template already exists')


def check_company_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    company = Company.query.filter(func.lower(Company.name)==field.data.lower()).first()
    if company:
        raise ValidationError('Company already exists')


def check_site_exists(form, field):
    if field.object_data:
        if field.object_data.lower() == field.data.lower():
            return
    site = Site.query.filter(func.lower(Site.name)==field.data.lower()).first()
    if site:
        raise ValidationError('Site already exists')


def check_alpha_code_exists(form, field):
    # checks new and current data when editing existing instance, returns if they are the same
    if field.object_data: # otherwise we get a NoneType Error when checking for lowercase
        if field.object_data.lower() == field.data.lower():
            return
    country = Country.query.filter(func.lower(Country.code)==field.data.lower()).first()
    if country:
        raise ValidationError('Alpha Code already exists')


def check_country_exists(form, field):
    if field.object_data:
        if field.object_data.lower() == field.data.lower():
            return
    country = Country.query.filter(func.lower(Country.name)==field.data.lower()).first()
    if country:
        raise ValidationError('Country already exists')
