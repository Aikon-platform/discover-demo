# Frontend

This folder contains the resources for the front-end server.

## Development

### Python setup

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

### Webpack setup

This project uses webpack to bundle the javascript and sass components (commited in `shared/static/`).

If you want to develop those components, you need first to [install npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm), for example by installing nvm, and then initializing npm:

    ```bash
    # Install nvm
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    # Install node
    nvm install node
    ```

You then need to initialize npm in the webpack folder, and install all required packages:

    ```bash
    cd webpack
    npm init
    ```

You can then start webpack compiler from the webpack folder:

    ```bash
    npx webpack --watch
    ```

**Note:** If you only need to update css, you can simply set up any sass compiler, to take as input `webpack/src/sass/style.scss` and output `shared/static/css/style.css`, it might be much quicker.

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