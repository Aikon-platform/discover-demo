# API

This folder contains the code for the API

## Development

Copy the file `.env.template` to a file `.env`. You should not need to change anything to it.

You need to install redis and python:

    sudo apt-get install redis-server python3-venv python3-dev

Create a python virtual environment and install the required packages:

    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt

You can now run the API worker:

    . venv/bin/activate
    celery -A app.app:celery worker -l INFO -c 1 -P threads

And the server:

    . venv/bin/activate
    flask --app app.app run --debug

## Production deployment

Copy the file `.env.template` to a file `.env`. Change it to `TARGET=prod`, and indicate the appropriate credentials.

Build the docker.