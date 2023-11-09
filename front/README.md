# Frontend

This folder contains the resources for the front-end server.

## Development

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

You need to install redis and python:

    ```bash
    sudo apt-get install redis-server python3-venv python3-dev
    ```

Create a python virtual environment and install the required packages:

    ```bash
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    ```

Initialize django:

    ```bash
    # Create a db.sqlite database
    ./venv/bin/python manage.py migrate
    # Create a superuser
    ./venv/bin/python manage.py createsuperuser
    ```


You can now run the frontend worker (meant for collecting API results, or doing cleanup tasks):

    ```bash
    ./venv/bin/python manage.py rundramatiq -p 1 -t 1
    ```

And the server:

    ```bash
    ./venv/bin/python manage.py runserver
    ```

You can now connect to [localhost:8000](http://localhost:8000/) and see the website.

## Production

### Initial deployment

You need to install redis, python, and supervisor:

    ```bash
    sudo apt-get install redis-server python3-venv python3-dev supervisord
    ```

Create a python virtual environment and install the required packages:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-prod.txt
    ```

Create a database using postgresl (or change the DATABASE [setting](demowebsite/settings/prod.py) to use another db backend):

    ```bash
    # Install postgresql
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    sudo apt update
    sudo apt install postgresql
    # Init database
    sudo -u postgres psql
    postgres=# CREATE DATABASE demowebsite;
    postgres=# CREATE USER demowebsite WITH PASSWORD '<password>';
    postgres=# ALTER ROLE demowebsite SET client_encoding TO 'utf8';
    postgres=# ALTER ROLE demowebsite SET default_transaction_isolation TO 'read committed';
    postgres=# ALTER ROLE demowebsite SET timezone TO 'UTC';
    postgres=# GRANT ALL PRIVILEGES ON DATABASE vhs TO demowebsite;
    postgres=# \q
    ```

Copy the file `.env.template` to a file `.env`. Change it to `TARGET=prod`, and indicate the appropriate credentials.

Initialize django:

    ```bash
    source venv/bin/activate
    # Create the database content
    python manage.py migrate
    # Collect the static files
    python manage.py collectstatic
    # Create a superuser
    python manage.py createsuperuser
    ```

You need to have a service that starts the server and automatically restarts it if it crashes, or stop, for any reason. You can set up a systemd service to do so:

    ```bash
    #TODO
    ```

And a web server (preferably nginx) setup that serves the static content, and the django website. (TODO)

### Updating

To update, please run all those commands :

    ```bash
    git pull
    source venv/bin/activate
    python manage.py migrate
    yes | python manage.py collectstatic
    ```

And then restart the systemd service.

    ```bash
    sudo service demowebsite restart
    ```