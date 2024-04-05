#! /bin/bash
[ ! -f .env.dev ] || export $(grep -v '^#' .env.dev | xargs)

(trap 'kill 0' SIGINT;
    (cd api/ && export CUDA_VISIBLE_DEVICES=$DEVICE_NB && venv/bin/flask --app app.main run --debug -p $API_DEV_PORT) &
    (cd api/ && venv/bin/dramatiq app.main -t 1 -p 1) &
    (cd front/ && venv/bin/python manage.py runserver $FRONT_DEV_PORT) &
    (cd front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1);
);
