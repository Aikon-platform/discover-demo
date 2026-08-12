DOCKER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FRONT_ROOT="$(dirname "$DOCKER_DIR")"

FRONT_ENV="$FRONT_ROOT/front/.env"
DOCKER_ENV="$FRONT_ROOT/docker/.env"

source "$FRONT_ROOT"/scripts/utils.sh

# if ../front/.env does not exist, create it
if [ ! -f $FRONT_ENV ]; then
    echo_title "SET UP FRONT ENV VARIABLES"
    cp $FRONT_ENV.template $FRONT_ENV
    update_env $FRONT_ENV
fi

# if docker/.env does not exist, create it
if [ ! -f $DOCKER_ENV ]; then
    echo_title "SET UP DOCKER ENV VARIABLES"
    cp $DOCKER_ENV.template $DOCKER_ENV
    update_env $DOCKER_ENV
fi

check_env() {
    local ENV_FILE=$1
    local HASH_FILE="${ENV_FILE}_hash"

    if [ ! -f "$ENV_FILE" ]; then
        color_echo red "Error: Environment file $ENV_FILE does not exist" >&2
        return 1
    fi

    local CURRENT_HASH=$(md5sum "$ENV_FILE" | awk '{print $1}')
    if [ ! -f "$HASH_FILE" ]; then
        echo "$CURRENT_HASH" > "$HASH_FILE"
        return 1
    fi

    local STORED_HASH=$(cat "$HASH_FILE")

    if [ "$STORED_HASH" != "$CURRENT_HASH" ]; then
        echo "$CURRENT_HASH" > "$HASH_FILE"
        return 1
    else
        return 0 # unchanged
    fi
}

check_env "$FRONT_ENV" || check_env "$DOCKER_ENV"
need_update=$?   # 1 means changed, 0 means unchanged

source $FRONT_ENV
source $DOCKER_ENV

# if $DATA_FOLDER does not exist
if [ ! -d "$DATA_FOLDER" ]; then
    echo_title "CREATE DATA FOLDER INSIDE $DATA_FOLDER"
    # Create $DATA_FOLDER folder with right permissions for user $USERID
    sudo mkdir -p "$DATA_FOLDER"
    sudo chown -R "$USERID:$USERID" "$DATA_FOLDER"
    sudo chmod -R 775 "$DATA_FOLDER"
fi

if [ $need_update -eq 1 ]; then
    color_echo yellow "Change detected in .env files. Updating configuration files..."
fi

# generate nginx config without SSL certificate for nginx image inside Docker
if [ $need_update -eq 1 ] || [ ! -f "$FRONT_ROOT"/docker/nginx_conf ] ; then
    echo_title "GENERATING INTERNAL DOCKER NGINX CONFIG"

    cp "$FRONT_ROOT"/docker/nginx.conf.template "$FRONT_ROOT"/docker/nginx_conf

    sed -i -e "s~DJANGO_PORT~$DJANGO_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed -i -e "s~NGINX_PORT~$NGINX_PORT~" "$FRONT_ROOT"/docker/nginx_conf
    sed -i -e "s~PROD_URL~$PROD_URL~" "$FRONT_ROOT"/docker/nginx_conf
    sed -i -e "s~USERNAME~aikondemo~" "$FRONT_ROOT"/docker/nginx_conf
fi

# generate nginx config with SSL certificate for outside Docker
if [ $need_update -eq 1 ] || [ ! -f "$FRONT_ROOT"/docker/nginx_ssl ] ; then
    echo_title "GENERATING EXTERNAL NGINX CONFIG"
    cp "$FRONT_ROOT"/docker/nginx.conf.ssl_template "$FRONT_ROOT"/docker/nginx_ssl

    sed -i -e "s~SSL_CERTIFICATE~$SSL_CERTIFICATE~" "$FRONT_ROOT"/docker/nginx_ssl
    sed -i -e "s~SSL_KEY~$SSL_KEY~" "$FRONT_ROOT"/docker/nginx_ssl
    sed -i -e "s~NGINX_PORT~$NGINX_PORT~" "$FRONT_ROOT"/docker/nginx_ssl
    sed -i -e "s~PROD_URL~$PROD_URL~" "$FRONT_ROOT"/docker/nginx_ssl
fi

if [ $need_update -eq 1 ] || [ ! -f "$FRONT_ROOT"/docker/supervisord.conf ] ; then
    echo_title "GENERATING SUPERVISORD CONFIG"
    cp "$FRONT_ROOT"/docker/supervisord.conf.template "$FRONT_ROOT"/docker/supervisord.conf

    sed -i -e "s/DJANGO_PORT/$DJANGO_PORT/g" "$FRONT_ROOT"/docker/supervisord.conf
fi
