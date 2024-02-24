#!/bin/bash
#
python ping.py    

make install

exec gunicorn -c 'python:conf.gunicorn' \
    --reload \
    'app.run:app'
