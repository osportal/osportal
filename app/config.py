from environ import environ
from os import urandom
from os.path import abspath, dirname, exists, join, pardir
import secrets


def gen_secret_key():
    """ Returns secret key """
    return secrets.token_hex(64)

def absolute_path(relative):
    """ Return an absolute path relative to the project root """
    return abspath(join(dirname(__file__),
        pardir, pardir, pardir,pardir, relative))


env = environ.Env(
        SECURE_PROXY_SSL_HEADER=(tuple, None)
)

if not env('IGNORE_ENV_FILE', default=False):
    project_env = absolute_path(".env")
    if exists(project_env):
        environ.Env.read_env(env_file=project_env)


DEBUG = env('DEBUG', default=True)
SERVER_NAME = env('SERVER_NAME', default='localhost:8002')
DEBUG_TB_INTERCEPT_REDIRECTS = env('DEBUG_TB_INTERCEPT_REDIRECTS', default=False)

SESSION_COOKIE_SECURE=env('SESSION_COOKIE_SECURE', default=True)
REMEMBER_COOKIE_SECURE=env('REMEMBER_COOKIE_SECURE', default=True)
SESSION_COOKIE_HTTPONLY=env('SESSION_COOKIE_HTTPONLY', default=True)
REMEMBER_COOKIE_HTTPONLY=env('REMEMBER_COOKIE_HTTPONLY', default=True)

SECRET_KEY = env('SECRET_KEY', default=gen_secret_key())
SERVER_PORT = env('SERVER_PORT', default=5000)
POSTGRES_USER = env('POSTGRES_USER', default='postgres')
POSTGRES_PASSWORD = env('POSTGRES_PASSWORD', default='postgres')
POSTGRES_DB = env('POSTGRES_DB', default='postgres')
POSTGRES_HOST = env('POSTGRES_HOST', default='localhost')
POSTGRES_PORT = env('POSTGRES_PORT', default=5432)
POSTGRES_URI = env('POSTGRES_URI', default=f'{POSTGRES_HOST}:{POSTGRES_PORT}')
UPLOAD_STORAGE_PATH = env('UPLOAD_STORAGE_PATH', default=None)

# Database
DB_URI = env('DB_URI', default=f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URI}/{POSTGRES_DB}')
#if not DB_URI:
#    DB_URI = 'sqlite:///site.db'
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = env('SQLALCHEMY_TRACK_MODIFICATIONS', default=False)

# CELERY
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://:devpassword@redis:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json', 'yaml', 'pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'json'
