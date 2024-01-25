#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

colorEcho() {
    Color_Off="\033[0m"
    Red="\033[1;91m"        # Red
    Green="\033[1;92m"      # Green
    Yellow="\033[1;93m"     # Yellow
    Blue="\033[1;94m"       # Blue
    Purple="\033[1;95m"     # Purple
    Cyan="\033[1;96m"       # Cyan

    case "$1" in
        "green") echo -e "$Green$2$Color_Off";;
        "red") echo -e "$Red$2$Color_Off";;
        "blue") echo -e "$Blue$2$Color_Off";;
        "yellow") echo -e "$Yellow$2$Color_Off";;
        "purple") echo -e "$Purple$2$Color_Off";;
        "cyan") echo -e "$Cyan$2$Color_Off";;
        *) echo "$2";;
    esac
}

colorEcho purple "\n\n=====================================\n======= REQUIREMENTS INSTALL ========\n====================================="

colorEcho yellow "\nOS packages ..."
sudo apt-get install redis-server python3.10 python3.10-venv python3.10-dev curl

colorEcho yellow "\nAPI virtual env ..."
python3.10 -m venv api/venv
api/venv/bin/pip install -r api/requirements.txt

colorEcho yellow "\nFront virtual env ..."
python3.10 -m venv front/venv
front/venv/bin/pip install -r front/requirements.txt

colorEcho purple "\n\n=====================================\n=== SET UP ENVIRONMENT VARIABLES ====\n====================================="
API_ENV="$SCRIPT_DIR"/api/.env
FRONT_ENV="$SCRIPT_DIR"/front/.env

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

prompt_user() {
    env_var=$(colorEcho 'red' "$1")
    default_val="$2"
    current_val="$3"
    if [  "$2" != "$3" ]; then
        default="Press enter for $(colorEcho 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        default="Press enter to keep $(colorEcho 'cyan' "$current_val")"
        default_val=$current_val
    fi

    read -p "$env_var"$'\n'"$default: " value
    echo "${value:-$default_val}"
}

get_env_value() {
    param=$1
    env_file=$2
    value=$(awk -F= -v param="$param" '/^[^#]/ && $1 == param {gsub(/"/, "", $2); print $2}' "$env_file")
    echo "$value"
}

update_env() {
    env_file=$1
    params=($(awk -F= '/^[^#]/ {print $1}' "$env_file"))
    for param in "${params[@]}"; do
        current_val=$(get_env_value "$param" "$env_file")
        case $param in
            *PASSWORD*)
                default_val="$(generate_random_string)"
                ;;
            *SECRET*)
                default_val="$(generate_random_string)"
                ;;
            *)
                default_val="$current_val"
                ;;
        esac

        new_value=$(prompt_user "$param" "$default_val" "$current_val")
        sed -i '' -e "s~^$param=.*~$param=\"$new_value\"~" "$env_file"
    done
}

cp "$API_ENV".template "$API_ENV"
cp "$FRONT_ENV".template "$FRONT_ENV"

colorEcho yellow "\nSetting API .env file ..."
update_env "$API_ENV"

colorEcho yellow "\nSetting Front .env file ..."
update_env "$FRONT_ENV"

. "$API_ENV"

if [ "$TARGET" == "dev" ]; then
    colorEcho purple "\n\n=====================================\n======== PRE-COMMIT INSTALL =========\n====================================="
    api/venv/bin/pip install pre-commit
    pre-commit install
fi

set_redis() {
    redis_psw="$1"
    REDIS_CONF=/etc/redis/redis.conf
    if [ ! -f "$REDIS_CONF" ]; then
        REDIS_CONF=/usr/local/etc/redis.conf # MacOs
    fi
    colorEcho yellow "\n\nModifying Redis configuration file $REDIS_CONF ..."

    # use the same redis password for api and front
    sed -i '' -e "s~^$REDIS_PASSWORD=.*~$REDIS_PASSWORD=\"$redis_psw\"~" "$FRONT_ENV"

    sudo sed -i -e "s/\nrequirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"
    sudo sed -i -e "s/# requirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"

    sudo systemctl restart redis
    # brew services restart redis # MacOs
}
# NOTE uncomment to use Redis password
# set_redis $REDIS_PASSWORD

colorEcho purple "\n\n=====================================\n===== DOWNLOADING DTI SUBMODULE =====\n====================================="
git submodule init
git submodule update

colorEcho purple "\n\n=====================================\n========= INITIALIZE DJANGO =========\n====================================="

. "$FRONT_ENV"

cd front
./venv/bin/python manage.py migrate

colorEcho yellow "\nCreating superuser\nusername: $ADMIN_NAME\nemail: $ADMIN_EMAIL\npassword: <same-as-db-password> ..."
echo "from django.contrib.auth.models import User; User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$DB_PASSWORD')" | ./venv/bin/python manage.py shell

colorEcho purple "\n\n=====================================\n=========== SETUP WEBPACK ===========\n====================================="

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

nvm install node
npm install -g webpack
npm install -g sass
npm install -D webpack-cli

cd webpack
colorEcho yellow "\nInit npm project inside $(pwd) ..."
npm init

npm run start
npm run production
