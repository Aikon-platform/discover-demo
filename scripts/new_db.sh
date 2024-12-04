SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

manage="$FRONT_VENV/python $FRONT_DIR/manage.py"

rm -rf "$FRONT_DIR/db.sqlite3"

manage makemigrations
bash "$SCRIPT_DIR"/database.sh
