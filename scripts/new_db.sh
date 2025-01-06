SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

manage="$FRONT_VENV/python $FRONT_DIR/manage.py"

echo_title "DELETE OLD DATABASE"
rm -rf "$FRONT_DIR/db.sqlite3"

# FOR POSTGRESQL DATABASES
# echo_title "DROPPING ALL TABLES"
# . "$FRONT_DIR"/.env
# PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
# DROP SCHEMA public CASCADE;
# CREATE SCHEMA public;
# GRANT ALL ON SCHEMA public TO $DB_USER;
# GRANT ALL ON SCHEMA public TO public;
# EOF

$manage makemigrations
bash "$SCRIPT_DIR"/database.sh
