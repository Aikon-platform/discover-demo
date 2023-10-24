# Frontend

This folder contains the code for the Frontend

## Development

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

You need to install redis and python:

    sudo apt-get install redis-server python3-venv python3-dev

Create a python virtual environment and install the required packages:

    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt

Initialize the django database:

    . venv/bin/activate
    python manage.py migrate

You can now run the API worker:

    . venv/bin/activate
    python manage.py rundramatiq -p 1 -t 1

And the server:

    . venv/bin/activate
    python manage.py runserver

You can now connect to [http://localhost:8000/] and see the website.

## Production deployment

Copy the file `.env.template` to a file `.env`. Change it to `TARGET=prod`, and indicate the appropriate credentials.
