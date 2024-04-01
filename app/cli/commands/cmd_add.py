from app import create_app
from app.extensions import db
from app.user.models import User, Role
from app.utils.populate import create_default_countries, create_user
from app.cli.utils import EmailType
import click
from datetime import datetime
from faker import Faker
import random
from sqlalchemy.exc import PendingRollbackError, IntegrityError

# Create an app context for the database connection.
app = create_app()
db.app = app
fake = Faker()


def _log_status(count, model_label):
    """
    Log the output of how many records were created.

    :param count: Amount created
    :type count: int
    :param model_label: Name of the model
    :type model_label: str
    :return: None
    """
    click.echo('Created {0} {1}'.format(count, model_label))

    return None


def _bulk_insert(model, data, label):
    """
    Bulk insert data to a specific model and log it. This is much more
    efficient than adding 1 row at a time in a loop.

    :param model: Model being affected
    :type model: SQLAlchemy
    :param data: Data to be saved
    :type data: list
    :param label: Label for the output
    :type label: str
    :param skip_delete: Optionally delete previous records
    :type skip_delete: bool
    :return: None
    """
    with app.app_context():
        if model.__name__ == 'User':
            # don't delete users
            pass
        else:
            model.query.delete()

        db.session.commit()
        db.engine.execute(model.__table__.insert(), data)

        _log_status(model.query.count(), label)

    return None


@click.group()
def cli():
    """ Add items to the database. """
    pass


@click.command()
def users():
    """
    Generate fake users.
    """
    random_emails = []
    data = []

    click.echo('Creating users...')

    # Ensure we get about 100 unique random emails.
    for i in range(0, 99):
        random_emails.append(fake.email())

    random_emails = list(set(random_emails))

    while True:
        if len(random_emails) == 0:
            break

        fake_datetime = fake.date_time_between(
            start_date='-1y', end_date='now').strftime('%s')

        created_on = datetime.utcfromtimestamp(
            float(fake_datetime)).strftime('%Y-%m-%dT%H:%M:%S Z')

        random_percent = random.random()

        email = random_emails.pop()

        random_percent = random.random()

        """
        if random_percent >= 0.5:
            random_trail = str(int(round((random.random() * 1000))))
            username = fake.first_name() + random_trail
        else:
            username = None
        """

        random_trail = str(int(round((random.random() * 1000))))
        username = fake.first_name() + random_trail

        params = {
            'created_on': created_on,
            'updated_on': created_on,
            'email': email,
            'username': username,
            'password': User.encrypt_password('password')
        }

        data.append(params)

    return _bulk_insert(User, data, 'users')


@click.command()
def countries():
    """ Create default countries """
    click.secho('[+] Creating countries...', fg='cyan')
    try:
        create_default_countries()
    except (IntegrityError, PendingRollbackError) as e:
        click.secho(f'{e.orig.diag.message_detail}', fg='red')
    except Exception as e:
        click.secho(f'{e}', fg='red')
    else:
        click.secho('[+] Created countries.', fg='cyan')


@click.command()
def user():
    ''' Create new user '''
    username = click.prompt(click.style('Username', fg='magenta'),
                            type=str)
    email = click.prompt(click.style('Email', fg='magenta'),
                         type=EmailType())
    password = click.prompt(click.style('Password', fg='magenta'),
                            hide_input=True,
                            confirmation_prompt=True)
    roles = [x.name for x in Role.query.all()]
    role = click.prompt(click.style('Role', fg='magenta'),
                        type=click.Choice(roles, case_sensitive=False)
                        )
    try:
        create_user(username, email, password, role)
    except Exception as e:
        click.secho(f'{e}', fg='red')
    else:
        click.secho('[+] New user added', fg='green', bold=True)


cli.add_command(users)
cli.add_command(user)
cli.add_command(countries)
