from app.extensions import db
from app.utils.populate import create_default_settings
import click
from flask.cli import with_appcontext
from sqlalchemy_utils.functions import database_exists, create_database
from sqlalchemy.exc import PendingRollbackError, IntegrityError
import sys
from sqlalchemy.exc import OperationalError
import time


def wait_for_db():
    timeout = 60
    start_time = time.time()
    while True:
        try:
            db.session.execute('SELECT 1')
            print("Database is ready!")
            break
        except OperationalError:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError("Database connection timeout.")
            print("Waiting for database...")
            time.sleep(1)


def setup():
    click.secho('[+] Creating Tables...', fg='cyan')
    wait_for_db()
    db.create_all()
    click.secho('[+] Creating Default Settings...', fg='cyan')
    try:
        create_default_settings()
    except (IntegrityError, PendingRollbackError) as e:
        click.secho(f'{e.orig.diag.message_detail}', fg='red')
        pass
    except Exception as e:
        click.secho(f'{e}', fg='red')
        pass
    else:
        click.secho('[+] osPortal has been successfully installed!', fg='green', bold=True)

# below runs without any arguments
@click.command()
@with_appcontext
def cli():
    """ Installs osportal with an interactive setup """
    click.secho('[+] Installing osPortal...', fg='cyan')
    if database_exists(db.engine.url):
        click.secho('Database already exists.', fg='red')
        #sys.exit(0)
    elif not database_exists(db.engine.url):
        click.secho('[+] Creating Database...', fg='cyan')
        create_database(db.engine.url)
        click.secho('[+] Database successfully created.', fg='cyan')
    setup()
