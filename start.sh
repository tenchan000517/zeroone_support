#!/bin/bash
source antenv/bin/activate
exec gunicorn --bind 0.0.0.0:8000 main:app
