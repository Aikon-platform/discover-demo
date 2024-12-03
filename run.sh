#! /bin/bash
[ ! -f .env.dev ] || export $(grep -v '^#' .env.dev | xargs)

cleanup() {
    kill 0
    wait
    echo "All processes terminated."
    exit 0
}
# kill processes on FRONT_DEV_PORT / API_DEV_PORT / dramatiq

trap cleanup SIGINT SIGTERM

(
    (cd api/ && bash run.sh) &
    (cd front/ && venv/bin/python manage.py runserver $FRONT_DEV_PORT) &
    (cd front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1);
)
