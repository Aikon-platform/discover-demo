#! /bin/bash
(trap 'kill 0' SIGINT;
    (cd api/ && . .env && export CUDA_VISIBLE_DEVICES=$DEVICE_NB && venv/bin/flask --app app.main run --debug -p $DEV_PORT) &
    (cd api/ && export dramatiq_prom_port="9195" && export dramatiq_prom_db=/home/albouys/dev-dtidemo/api/tmp/ && venv/bin/dramatiq app.main -t 1 -p 1) &
    (cd front/ && venv/bin/python manage.py runserver) &
    (cd front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1);
);
