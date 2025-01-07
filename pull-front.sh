ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$ROOT_DIR/scripts/utils.sh"

(
    git pull &&
    cd front/ &&
    color_echo "yellow" "\nPython dependencies update" &&
    source venv/bin/activate &&
    pip install --upgrade pip &&
    pip install -r requirements-prod.txt &&
    color_echo "yellow" "\nDjango database migration & static collection" &&
    python manage.py migrate &&
    python manage.py collectstatic --noinput &&
    color_echo "yellow" "\nWeb server restart" &&
    sudo service apache2 restart &&
    sudo service dramatiq restart &&
    color_echo "green" "\n\nUpdate successful!"
)
