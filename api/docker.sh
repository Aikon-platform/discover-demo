#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

. "$SCRIPT_DIR/app/shared/.env.prod"

# MODIFY DEFAULT VALUES TO MATCH YOUR SYSTEM
# TODO mutualize data folder for all installed apps
DATA_FOLDER=${DATA_FOLDER:-"/media/discoverdemo/data/"}
DEVICE_NB=${DEVICE_NB:-3}
DEMO_UID=${DEMO_UID:-$(id -u)}

# Convert INSTALLED_APPS into an array
#IFS=',' read -ra INSTALLED_APPS <<< "$INSTALLED_APPS"

CONTAINER_NAME="demowebsiteapi"

# Check if the user with uid is part of the docker group
if ! id -nG "$DEMO_UID" | grep -qw docker; then
    echo "Adding user with UID $DEMO_UID to the docker group"
    sudo usermod -aG docker "$DEMO_UID"
fi

rebuild_image() {
    docker build --rm -t "$CONTAINER_NAME" . -f Dockerfile --build-arg USERID=$DEMO_UID
    cd ../
}

# if container exists and stop it
if docker ps -a --format '{{.Names}}' | grep -Eq "$CONTAINER_NAME"; then
    docker stop "$CONTAINER_NAME"
fi

if [ "$1" = "rebuild" ]; then
    rebuild_image
fi

if [ "$1" = "pull" ]; then
    git pull
    rebuild_image
fi

docker rm "$CONTAINER_NAME"

# Run Docker container
docker run -d --gpus "$DEVICE_NB" --name "$CONTAINER_NAME" \
   -v "$DATA_FOLDER":/data/ -p 127.0.0.1:8001:8001 \
   --restart unless-stopped --ipc=host "$CONTAINER_NAME"
