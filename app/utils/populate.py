from app.models import Country
from app.admin.models import Settings
from app.event.models import EventType
from app.pages.models import Page
from app.user.models import User, Role, Permission
from app.utils.countries import COUNTRIES_DICT
from sqlalchemy.exc import IntegrityError
import sys


def create_default_roles():
    su_params = {
            'name': 'Superuser',
            'description': 'I am God',
            'superuser': True
    }
    member_params = {
            'name': 'Member',
            'description': 'Standard User',
            'superuser': False
    }
    Role(**su_params).save()
    Role(**member_params).save()


def create_default_event_types():
    # default name and deductable values
    types = [
            ("Holiday", True, 14),
            ("Sickness", False, 7)
    ]
    for event_type in types:
        params = {
            'name': event_type[0],
            'deductable': event_type[1],
            'max_days': event_type[2]
        }
        EventType(**params).save()


def create_default_countries():
    for country in COUNTRIES_DICT.items():
        params = {
        'code': country[0],
        'name': country[1]
        }
        Country(**params).save()


def create_default_settings():
    create_default_roles()
    create_default_event_types()
    create_default_countries()
    params = {
        'id': 1,
        'site_name': 'osPortal'
    }
    return Settings(**params).save()


def create_user(username, email, password, role_name):
    role = Role.query.filter(Role.name==role_name).first()
    params = {
        'username': username,
        'email': email,
        'password': password,
        'role': role
    }
    return User(**params).save()
