#! /bin/bash
[ ! -f .env.dev ] || export $(grep -v '^#' .env.dev | xargs)

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cleanup() {
    kill 0
    wait
    echo "All processes terminated."
    exit 0
}
# kill processes on FRONT_DEV_PORT / API_DEV_PORT / dramatiq

trap cleanup SIGINT SIGTERM

# (
#     (cd api/ && bash run.sh) &
#     (cd front/ && venv/bin/python manage.py runserver $FRONT_DEV_PORT) &
#     (cd front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1);
# )

cd $ROOT_DIR/api/ && bash run.sh &
api_pid=$!
cd $ROOT_DIR/front/ && venv/bin/python manage.py runserver $FRONT_DEV_PORT &
front_server_pid=$!
cd $ROOT_DIR/front/ && venv/bin/python manage.py rundramatiq -t 1 -p 1 &
front_dramatiq_pid=$!

wait $api_pid $front_server_pid $front_dramatiq_pid
