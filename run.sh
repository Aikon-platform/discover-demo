#! /bin/bash
(trap 'kill 0' SIGINT;
    (. api/app/shared/.env && export CUDA_VISIBLE_DEVICES=$DEVICE_NB) &
    (cd api/ && venv/bin/flask --app app.main run --debug -p $DEV_PORT) &
    (cd api/ && venv/bin/dramatiq app.main -t 1 -p 1) &
    (cd front/ && venv/bin/python manage.py runserver) &
    (cd front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1);
);
