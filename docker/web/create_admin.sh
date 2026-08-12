DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

source "$FRONT_ROOT"/scripts/utils.sh

name=${1:-"admin"}
psw=${2:-$(generate_random_string)}
email=${3:-"$name@mail.com"}

manage="/home/aikondemo/venv/bin/python /home/aikondemo/app/manage.py"

echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
username = '$name';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, '$email', '$psw');
    print('Superuser created.');
else:
    print('Superuser already exists.');
" | $manage shell

echo '\nConnect to app using:'
echo -e "          👤 $name"
echo -e "          🔑 $psw"
