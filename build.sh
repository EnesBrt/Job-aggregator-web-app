#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static asset files
python ./job-aggregator-web-app/manage.py collectstatic --no-input

# Apply any outstanding database migrations
python ./job-aggregator-web-app/manage.py migrate
