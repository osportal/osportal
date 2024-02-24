from app.models import Country
from app.admin.models import Settings
from app.event.models import EventType
from app.pages.models import Page
from app.user.models import User, Role, Permission
from app.utils.countries import COUNTRIES_DICT
from sqlalchemy.exc import IntegrityError
import sys


def create_default_permissions():
    post_permission_params = {
            'name': 'postCRUD',
            'db_name': 'post',
            'create': True,
            'read': True,
            'update': True,
            'delete': True
            }
    comment_permission_params = {
            'name': 'commentCRUD',
            'db_name': 'comment',
            'create': True,
            'read': True,
            'update': True,
            'delete': True
            }
    Permission(**post_permission_params).save()
    Permission(**comment_permission_params).save()


def create_default_roles():
    create_default_permissions()
    post_crud = Permission.query \
                .filter(Permission.name=='postCRUD').first()
    comment_crud = Permission.query \
                   .filter(Permission.name=='commentCRUD').first()
    su_params = {
            'name': 'Superuser',
            'description': 'I am God',
            'superuser': True
    }
    member_params = {
            'name': 'Member',
            'description': 'Standard User',
            'permissions': [post_crud, comment_crud]
    }
    Role(**su_params).save()
    Role(**member_params).save()


def create_default_event_types():
    # default name and deductable values
    types = [
            ("Holiday", True),
            ("Sickness", False)
    ]
    for event_type in types:
        params = {
            'name': event_type[0],
            'deductable': event_type[1]
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


"""
def create_superuser(username, email, password):
    params = {
        'username': username,
        'email': email,
        'password': password
    }
    return User(**params).save()
"""
