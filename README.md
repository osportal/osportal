<img src='app/static/img/logo/vector/default-monochrome.svg' style="width:790px; height:260px; margin-bottom: 50px;"/>

[osPortal](https://osportal.com) is a free and open source Intranet platform built with Python. 

## Install

### Docker

Make sure both [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/) are installed.

1. Create a blank .env file. You can modify it to your liking.

2. Run `docker-compose up -d` to install and launch the services.

The site will be running on `localhost:8002`

First time setup will prompt you to add a new admin account.

You can monitor your celery workers and tasks via Flower, which can be accessed via `localhost:5555`

Flower credentials: `admin:password`

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
