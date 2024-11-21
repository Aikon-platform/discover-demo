#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

set_redis() {
    redis_psw="$1"
    REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
    color_echo yellow "\n\nModifying Redis configuration file $REDIS_CONF..."

    # use the same redis password for api and front
    $SED_CMD "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=\"$redis_psw\"~" "$FRONT_ENV"

    sudo $SED_CMD "s/\nrequirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"
    sudo $SED_CMD "s/# requirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"

    case $OS in
        Linux)   sudo systemctl restart redis ;;
        Mac)     brew services restart redis ;;
        Windows) net start redis ;;
    esac
}

# color_echo yellow "\nSetting Redis password..."
# set_redis $REDIS_PASSWORD
