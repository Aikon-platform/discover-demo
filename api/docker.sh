#!/bin/bash

# MODIFY THOSE VARIABLES TO MATCH YOUR SYSTEM
DATA_FOLDER="/media/dyonisos/data/dtidemo/"
DEMO_UID=1019
DEVICE_NB=3

CONTAINER_NAME="demowebsiteapi"

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
