<img src='app/static/img/logo/vector/default-monochrome.svg' style="width:790px; height:260px; margin-bottom: 50px;"/>

[osPortal](https://osportal.com) is a free and open source Intranet platform built with Python. 

## Self-Hosted

Run the following commands:
```
git clone https://github.com/osportal/osportal.git
cd osportal
```

### Docker

Make sure both [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/) are installed.

1. Create a blank .env file. You can modify it to your liking.

2. To install and launch the services:
   ```docker-compose up -d```

The site will be running on `localhost:8000`

First time setup will prompt you to add a new admin account.

You can monitor your celery workers and tasks via Flower, which can be accessed via `localhost:5555`

Flower credentials: `admin:password`

### Manual Install

1. Create a .env file. Override app/config.py variables if needed, for example:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=exampleuser
POSTGRES_PASSWORD=examplepassword
POSTGRES_DB=exampledb
```

2. Create a Python virtual environment: ```python -m venv venv```

3. Activate the virtual environment: ```source venv/bin/activate```

4. Install dependencies and osportal: ```make install```

5. Run the server: ```gunicorn --config conf/gunicorn.py app.run:app```


## Updating DB Schema with Flask-Migrate

Tell Migrate and Alembic that the database is up to date, with the stamp command:
```
flask db stamp head 
```

Generate an initial migration:
```
flask db migrate
```

Finally, apply the migration:
```
flask db upgrade
```
