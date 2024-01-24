#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

API_ENV="$SCRIPT_DIR"/api/.env
FRONT_ENV="$SCRIPT_DIR"/front/.env

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

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
    # value=$(grep -oP "(?<=^$param=\")[^\"]*" "$env_file")
    value=$(awk -F= -v param="$param" '/^[^#]/ && $1 == param {gsub(/"/, "", $2); print $2}' "$env_file")
    echo "$value"
}

update_env() {
    env_file=$1
    # params=($(grep -oP '^[^#].*=' "$env_file" | cut -d= -f1))
    params=($(awk -F= '/^[^#]/ {print $1}' "$env_file"))
    for param in "${params[@]}"; do
        current_val=$(get_env_value "$param" "$env_file")
        # TODO reuse REDIS_PASSWORD twice
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

colorEcho yellow "\n\nSetting API .env file"
update_env "$API_ENV"

colorEcho yellow "\n\nSetting Front .env file"
update_env "$FRONT_ENV"

# NOTE uncomment to use Redis password
#REDIS_CONF=/etc/redis/redis.conf
#if [ ! -f "$REDIS_CONF" ]; then
#  REDIS_CONF=/usr/local/etc/redis.conf # MacOs
#fi
#
#colorEcho yellow "\n\nModifying Redis configuration file $REDIS_CONF"
#
#. "$API_ENV"
#sudo sed -i -e "s/\nrequirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
#sudo sed -i -e "s/# requirepass [^ ]*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
#
# Reload Redis
# brew services restart redis

