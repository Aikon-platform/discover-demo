(
    git pull &&
    cd front/ &&
    source venv/bin/activate &&
    pip install -r requirements-prod.txt &&
    python manage.py migrate &&
    python manage.py collectstatic --noinput &&
    sudo service apache2 restart &&
    sudo service dramatiq restart
)