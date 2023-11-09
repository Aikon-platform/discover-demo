docker kill demowebsiteapi;
if [ "$1" = "rebuild" ]; then
    docker build --rm -t demowebsiteapi . -f Dockerfile;
    cd ../;
fi;

if [ "$1" = "pull" ]; then
    cd explore/;
    git pull;
    docker build --rm -t demowebsiteapi . -f Dockerfile;
    cd ../;
fi;

docker run -d --rm --gpus all --name demowebsiteapi \
   -v /home/demowebsiteapi/data/:/data/ \
   -u 1001:1001 demowebsiteapi