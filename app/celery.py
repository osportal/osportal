from app import create_celery_app
#from flask import current_app

from app.run import app

celery = create_celery_app(app)
