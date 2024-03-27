#! /bin/bash
(trap 'kill 0' SIGINT;
    (cd api/ && . .env && export CUDA_VISIBLE_DEVICES=$DEV_GPU) &
    (venv/bin/flask --app app.main run --debug -p "$DEV_PORT") &
    (cd api/ && venv/bin/dramatiq app.main -p 1 -t 1) &
    (cd front/ && venv/bin/python manage.py runserver) &
    (cd front/ && venv/bin/python manage.py rundramatiq -p 1 -t 1);
);
