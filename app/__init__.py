from celery import Celery
from datetime import datetime
from elasticsearch import Elasticsearch
from flask import Flask, url_for, Blueprint, g, current_app, redirect, render_template, request
from flask_login import current_user
import jinja2
import logging
from logging.handlers import SMTPHandler
import os
import traceback
from werkzeug.middleware.proxy_fix import ProxyFix

# Routes
from app.main.routes import main
from app.user.routes import user
from app.user import update_user_jinja_globals
from app.admin.routes import admin
from app.admin import update_admin_jinja_globals
from app.event.routes import event
from app.department.routes import department
from app.pages.routes import pages
from app.pages import update_pages_jinja_globals
from app.posts.routes import posts
# Models
from app.admin.models import Settings, Page
from app.event.models import EventType
from app.user.models import User
# Utils
from app.utils.populate import create_default_settings

from app.extensions import (
        db,
        login_manager,
        mail,
        migrate,
        debug_toolbar,
)
from app.plugins import init_plugins


CELERY_TASK_LIST = [
    'app.tasks',
    'app.email',
    'app.user.tasks',
]

def create_celery_app(app):
    """
    Create a new Celery object and tie together the Celery config
    to the app's config. Wrap all tasks in the context of the app

    :param app: Flask app
    :return: Celery app
    """
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASK_LIST)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract=True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app():
    app = Flask(__name__,
                instance_relative_config=True,
                template_folder='templates',
                static_folder='static')
    app.config.from_object('app.config')
    app.register_blueprint(admin)
    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(event)
    app.register_blueprint(posts)
    app.register_blueprint(pages)
    app.register_blueprint(department)
    extensions(app)
    update_admin_jinja_globals(app)
    update_pages_jinja_globals(app)
    update_user_jinja_globals(app)
    authentication(app, User)
    middleware(app)
    error_templates(app)
    # create tables if they do not exist
    with app.app_context():
        db.create_all()
    return app


def extensions(app):
    """ Initialize 1 or more extensions """
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True, compare_type=True)
    mail.init_app(app)
    debug_toolbar.init_app(app)
    with app.app_context():
        init_plugins(app)

    return None


def authentication(app, user_model):
    login_manager.login_view = 'user.login'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(uid):
        user = user_model.query.get(uid)
        if user:
            if user.is_active():
                return user_model.query.get(uid)
            else:
                # logs user out if not active
                return None
        else:
            return None


def middleware(app):
    """
    Register 0 or more middleware (mutates the app passed in).
    :param app: Flask application instance
    :return: None
    """
    # Swap request.remote_addr with the real IP address even if behind a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app,
                            x_for=1,
                            x_proto=1,
                            x_host=1,
                            x_prefix=1)
    return None


def error_templates(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template('errors/405.html'), 405

    @app.errorhandler(413)
    def too_large(error):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        error_tb = traceback.format_exc()
        subject=('osPortal 500')
        try:
            # avoid circular import error
            from app.email import send_alert_email
            send_alert_email.delay(subject, error_tb)
        except Exception as e:
            print(e)
        return render_template('errors/500.html'), 500
