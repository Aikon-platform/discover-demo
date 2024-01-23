# Frontend

This folder contains the resources for the front-end server.

## Development

### Python setup

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

```bash
cp ./.env{.template,}
```

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
# Install webpack
npm install -g webpack
```

You then need to initialize npm in the webpack folder, and install all required packages:

```bash
cd webpack
npm init
```

You can then start webpack compiler from the webpack folder:

```bash
npm run start
```

It's better to commit production static files. To generate them, run:

```bash
npm run production
```

**Note:** If you only need to update css, you can simply set up any sass compiler, to take as input `webpack/src/sass/style.scss` and output `shared/static/css/style.css`, it might be much quicker.

```bash
# For example
npm install -g sass
sass webpack/src/sass/style.scss shared/static/css/style.css
```

## Production

### Initial deployment

You need to install redis, python, and supervisor:

```bash
sudo apt-get install redis-server python3-venv python3-dev
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
postgres=# CREATE DATABASE discover;
postgres=# CREATE USER discover WITH PASSWORD '<password>';
postgres=# ALTER ROLE discover SET client_encoding TO 'utf8';
postgres=# ALTER ROLE discover SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE discover SET timezone TO 'UTC';
postgres=# ALTER DATABASE discover OWNER TO discover;
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

### Services and server

You have several options to create the service that starts the program and automatically restarts it if it crashes.

If you're using nginx as a webserver, the best option is to use gunicorn, and start with either through supervisord, or as a systemd service.

If you prefer apache2, you can also use gunicorn this way (and configure a proxy pass in apache), or directly use apache's mod_wsgi.

The discover-demo runs this way. To install it, follow the [official documentation](https://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html). A few tips:

  - when running `configure`, do `./configure --with-python=/usr/bin/python3`
  - at the step "Loading Module Into Apache", the conf file should be `/etc/apache2/apache2.conf`

You then need to configure the web server (nginx or apache2) to serve the static content (media and static). See [django doc example](https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/modwsgi/#serving-files)

Due to a [bug with UUID](https://stackoverflow.com/questions/45990550/valid-uuid-is-not-a-valid-uuid), add `WSGIApplicationGroup %{GLOBAL}` to the apache2 conf.

Lastly, you need to configure a service to run the dramatiq daemon. For instance write the following `/etc/systemd/system/dramatiq.service`

```
[Unit]
Description=DramatiQ worker for Discover demo
Wants=network-online.target
After=network-online.target
Requires=redis.service
StartLimitIntervalSec=60

[Service]
WorkingDirectory=/home/discover/website/front/
ExecStart=/home/discover/website/front/venv/bin/python manage.py rundramatiq -p 1 -t 1
User=www-data
Group=www-data
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then :

```bash
systemctl enable dramatiq.service
service redis start
service dramatiq start
```

### Link with API

The front-end has to connect to the API server. You need to define `DTI_API_URL` to do so.

A good thing is to tunnel securely the connection between both. For `discover-demo.enpc.fr`, it is done with `spiped`, based on [this tutorial](https://www.codeflow.site/fr/article/how-to-encrypt-traffic-to-redis-with-spiped-on-ubuntu-16-04) (with target ports 8001, in service `spiped-connect` on frontend server and `spiped-dti` on worker).

### Updating

To update, please run all those commands :

```bash
git pull
source venv/bin/activate
python manage.py migrate
yes | python manage.py collectstatic
```

And then restart the services, with 

```bash
sudo service apache2 restart
sudo service dramatiq restart
```
