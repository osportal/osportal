from app.models import Country
from app.admin.models import Settings
from app.leave.models import LeaveType
from app.pages.models import Page
from app.user.models import User, Role, Permission
from app.utils.countries import COUNTRIES_DICT
from sqlalchemy.exc import IntegrityError
import sys


def create_default_roles():
    su_params = {
            'name': 'osportal',
            'description': 'This role is granted superuser privileges.',
            'superuser': True
    }
    member_params = {
            'name': 'member',
            'description': 'Standard user',
            'superuser': False
    }
    Role(**su_params).save()
    Role(**member_params).save()


def create_default_leave_types():
    # default name and deductable values
    types = [
            ("Holiday", True, True),
            ("Sickness", False, False)
    ]
    for leave_type in types:
        params = {
            'name': leave_type[0],
            'deductable': leave_type[1],
            'approval': leave_type[2]
        }
        LeaveType(**params).save()


def create_default_countries():
    for country in COUNTRIES_DICT.items():
        params = {
        'code': country[0],
        'name': country[1]
        }
        Country(**params).save()


def create_default_settings():
    create_default_roles()
    create_default_leave_types()
    create_default_countries()
    params = {
        'id': 1,
        'osportal_name': 'osPortal'
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
