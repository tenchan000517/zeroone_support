#!/bin/bash

echo "Starting the application with Gunicorn..."
gunicorn --bind 0.0.0.0:8000 kumosan:app
