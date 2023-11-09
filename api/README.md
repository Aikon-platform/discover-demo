# API

This folder contains the code for the worker API.

## Development

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

You need to install redis and python:

    ```bash
    sudo apt-get install redis-server python3-venv python3-dev
    ```

Create a python virtual environment and install the required packages:

    ```bash
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ```

You can now run the API worker:

    ```bash
    ./venv/bin/dramatiq app.main -p 1 -t 1
    ```

And the server:

    ```bash
    ./venv/bin/flask --app app.main run --debug
    ```

## Production deployment

Copy the file `.env.template` to a file `.env`. Change it to `TARGET=prod`, and indicate the appropriate credentials.

Build the docker.