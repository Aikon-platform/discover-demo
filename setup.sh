#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

color_echo() {
    Color_Off="\[\033[0m\]"
    Red="\[\033[1;91m\]"
    Green="\[\033[1;92m\]"
    Yellow="\[\033[1;93m\]"
    Blue="\[\033[1;94m\]"
    Purple="\[\033[1;95m\]"
    Cyan="\[\033[1;96m\]"

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

echo_title(){
    sep_line="========================================"
    len_title=${#1}

    if [ "$len_title" -gt 40 ]; then
        sep_line=$(printf "%0.s=" $(seq 1 $len_title))
        title="$1"
    else
        diff=$((38 - len_title))
        half_diff=$((diff / 2))
        sep=$(printf "%0.s=" $(seq 1 $half_diff))

        if [ $((diff % 2)) -ne 0 ]; then
            title="$sep $1 $sep="
        else
            title="$sep $1 $sep"
        fi
    fi

    color_echo purple "\n\n$sep_line\n$title\n$sep_line"
}

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

prompt_user() {
    env_var=$(color_echo 'red' "$1")
    default_val="$2"
    current_val="$3"
    desc="$4"

    if [ "$2" != "$3" ]; then
        default="Press enter for $(color_echo 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        default="Press enter to keep $(color_echo 'cyan' "$current_val")"
        default_val=$current_val
    fi

    read -p "$env_var $desc"$'\n'"$default: " value
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
    IFS=$'\n' read -d '' -r -a lines < "$env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$env_file")

            # Extract description from previous line if it exists
            desc=""
            if [[ $prev_line =~ ^# ]]; then
                desc=$(echo "$prev_line" | sed 's/^#\s*//')
            fi

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

            new_value=$(prompt_user "$param" "$default_val" "$current_val" "$desc")
            sed -i -e "s~^$param=.*~$param=\"$new_value\"~" "$env_file"
        fi
        prev_line="$line"
    done
}

set_redis() {
    redis_psw="$1"
    REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
    color_echo yellow "\n\nModifying Redis configuration file $REDIS_CONF..."

    # use the same redis password for api and front
    sed -i '' -e "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=\"$redis_psw\"~" "$FRONT_ENV"

    sudo sed -i -e "s/\nrequirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"
    sudo sed -i -e "s/# requirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"

    sudo systemctl restart redis
    # brew services restart redis # MacOs
}

echo_title "DOWNLOADING API SUBMODULE"
git submodule init
git submodule update
cd api && git submodule init && git submodule update && cd ..


echo_title "REQUIREMENTS INSTALL"
color_echo yellow "\nSystem packages..."
sudo apt-get install redis-server python3.10 python3.10-venv python3.10-dev curl

color_echo yellow "\nAPI virtual env..."
python3.10 -m venv api/venv
api/venv/bin/pip install --upgrade pip
api/venv/bin/pip install -r api/requirements.txt
api/venv/bin/pip install python-dotenv

color_echo yellow "\nFront virtual env..."
python3.10 -m venv front/venv
front/venv/bin/pip install --upgrade pip
front/venv/bin/pip install -r front/requirements.txt


echo_title "SET UP ENVIRONMENT VARIABLES"
API_ENV="$SCRIPT_DIR"/api/.env
FRONT_ENV="$SCRIPT_DIR"/front/.env
DEV_ENV="$SCRIPT_DIR"/.env.dev
cp "$API_ENV".template "$API_ENV"
cp "$FRONT_ENV".template "$FRONT_ENV"
cp "$DEV_ENV".template "$DEV_ENV"

color_echo yellow "\nSetting $API_ENV..."
update_env "$API_ENV"
. "$API_ENV"
if [ "$TARGET" == "dev" ]; then
    echo_title "PRE-COMMIT INSTALL"
    api/venv/bin/pip install pre-commit
    pre-commit install
fi

# NOTE uncomment to use Redis password
# color_echo yellow "\nSetting Redis password..."
# set_redis $REDIS_PASSWORD

color_echo yellow "\nSetting $FRONT_ENV file..."
update_env "$FRONT_ENV"


echo_title "INITIALIZE DJANGO"
. "$FRONT_ENV"
cd front
./venv/bin/python manage.py migrate

color_echo yellow "\nCreating superuser\nusername: $ADMIN_NAME\nemail: $ADMIN_EMAIL\npassword: <same-as-db-password>..."
echo "from django.contrib.auth.models import User; User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$DB_PASSWORD')" | ./venv/bin/python manage.py shell


echo_title "SETUP WEBPACK"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# BUG not working from there
nvm install node
sudo apt install npm
npm install -g webpack
npm install -g sass
npm install -D webpack-cli
cd webpack

color_echo yellow "\nInit npm project inside $(pwd)..."
npm init
npm install
npm run start
npm run production
