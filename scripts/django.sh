#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

manage="$FRONT_DIR/venv/bin/python $FRONT_DIR/manage.py"

echo_title "INITIALIZE DJANGO"
. "$FRONT_ENV"
"$FRONT_VENV"/python manage.py migrate

create_superuser() {
    echo "from django.contrib.auth import get_user_model; \
    User = get_user_model(); \
    User.objects.filter(username='$ADMIN_NAME').exists() or \
    User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$DB_PASSWORD')" | \
    "$FRONT_VENV"/python "$FRONT_DIR"/manage.py shell
}

color_echo yellow "\nCreating superuser\nusername: $ADMIN_NAME\nemail: $ADMIN_EMAIL\npassword: <same-as-db-password>..."
# create_superuser
echo "from django.contrib.auth.models import User; User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$DB_PASSWORD')" | "$FRONT_VENV"/python "$FRONT_DIR"/manage.py shell