#!/bin/bash

set -e

ENV_PATH="/home/aikondemo/app/.env"
source "$ENV_PATH"

# function to print an error log if connection to the database fails.
# the most probable error case is that a previous user was created with
# a different password => suggest a fix
psql_error_log () {
    error_log="$1"
    env_contents="$(cat "$ENV_PATH")"

    cat <<EOF
❌ ERROR when connecting to database !

📜 full error log:
$error_log

⚠️ this is likely due to a stale database user with a different password.

to reset the PostgreSQL user password, run:
    docker exec -it aikondemo-db-1 psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
to update Django superuser password, run:
    python run.py build && docker exec -it aikondemo-web-1 .venv/bin/python ./manage.py update_admin_password

🗝️ .env used to connect to the database:
$env_contents

exiting...
EOF
    exit 1
}

# --------------------------------------------

manage="uv run --directory=/home/aikondemo/app /home/aikondemo/app/manage.py"

echo ""
echo "collecting staticfiles..."
$manage collectstatic --noinput
echo "✅ staticfiles collected"

# # $manage makemigrations
# $manage migrate
#
# # Create superuser if it doesn't exist
# echo "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# username = '$POSTGRES_USER';
# if not User.objects.filter(username=username).exists():
#     User.objects.create_superuser(username, '$DEFAULT_FROM_EMAIL', '$POSTGRES_PASSWORD');
#     print('Superuser created.');
# else:
#     print('Superuser already exists.');
# " | $manage shell
# Run migrations with error handling
echo ""
echo "running migrations..."
if ! migration_output=$($manage migrate 2>&1); then
    psql_error_log "$migration_output";
fi
echo "✅ migrations completed"

# Create superuser if it doesn't exist with error handling
echo "creating superuser..."
if ! superuser_output=$(echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
username = '$POSTGRES_USER';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, '$DEFAULT_FROM_EMAIL', '$POSTGRES_PASSWORD');
    print('Superuser created.');
else:
    print('Superuser already exists.');
" | $manage shell 2>&1); then
    psql_error_log "$superuser_output" "$hashed_password"
fi
# TODO MAKE COMMAND TO UPDATE admin password in database, FOLLOWING THE $POSTGRES_PASSWORD, taking into account PASSWORD HASH
echo "✅ superuser setup completed"

echo ""
echo "✅ all startup tasks completed successfully!"
echo ""
echo "connect to app using:"
echo -e "          👤 $POSTGRES_USER"
echo -e "          🔑 $POSTGRES_PASSWORD"
echo ""
