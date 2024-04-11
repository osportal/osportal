#!/bin/bash
#
python ping.py    

make install

exec gunicorn -c 'python:conf.gunicorn' \
    --log-level 'debug' \
    --reload \
    'app.run:app' \
