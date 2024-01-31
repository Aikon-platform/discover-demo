# MODIFY THOSE VARIABLES TO MATCH YOUR SYSTEM
DATA_FOLDER=/media/dyonisos/data/dtidemo/
DEMO_UID=1019


docker kill demowebsiteapi;
if [ "$1" = "rebuild" ]; then
    docker build --rm -t demowebsiteapi . -f Dockerfile --build-arg USERID=$DEMO_UID;
    cd ../;
fi;

if [ "$1" = "pull" ]; then
    git pull;
    docker build --rm -t demowebsiteapi . -f Dockerfile --build-arg USERID=$DEMO_UID;
    cd ../;
fi;

docker rm demowebsiteapi

docker run -d --gpus 1 --name demowebsiteapi \
   -v $DATA_FOLDER:/data/ -p 127.0.0.1:8001:8001 \
   --restart unless-stopped --ipc=host demowebsiteapi
