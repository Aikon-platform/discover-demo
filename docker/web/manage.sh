#!/bin/bash

set -e

manage="uv run --directory=/home/aikondemo/app /home/aikondemo/app/manage.py"

$manage collectstatic --noinput

# $manage makemigrations
$manage migrate

# source /home/aikondemo/app/.env
# # Create superuser if it doesn't exist
# echo "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# username = '$ADMIN_NAME';
# if not User.objects.filter(username=username).exists():
#     User.objects.create_superuser(username, '$ADMIN_EMAIL', '$POSTGRES_PASSWORD');
#     print('Superuser created.');
# else:
#     print('Superuser already exists.');
# " | $manage shell
#
# echo '\nConnect to app using:'
# echo -e "          👤 $ADMIN_NAME"
# echo -e "          🔑 $POSTGRES_PASSWORD"
