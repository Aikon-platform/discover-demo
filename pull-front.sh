ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$ROOT_DIR/scripts/utils.sh"

(
    git pull &&
    cd front/ &&
    source venv/bin/activate &&
    pip install -r requirements-prod.txt &&
    python manage.py migrate &&
    python manage.py collectstatic --noinput &&
    sudo service apache2 restart &&
    sudo service dramatiq restart &&
    color_echo "green" "Update successful!"
)
