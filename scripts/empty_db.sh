#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

. "$FRONT_DIR"/.env

# Tables to truncate
tables=(
   "dticlustering_dticlustering"
   "dticlustering_savedclustering"
   "regions_regions"
   "similarity_similarity"
   "watermarks_watermarkprocessing"
)

for table in "${tables[@]}"; do
   psql -d $DB_NAME -c "TRUNCATE TABLE ${table} CASCADE;"
   color_echo "yellow" "Truncated ${table}"
done
