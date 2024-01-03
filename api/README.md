# API

This folder contains the code for the worker API.

## Development

```bash
cd api
```

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

```bash
cp ./.env{.template,}
```

You need to install redis and python:

```bash
sudo apt-get install redis-server python3-venv python3-dev
# brew install redis
# brew services start redis
```

You need to init the similarity submodule (and have the access to the [SimilarityDetection](https://github.com/Segolene-Albouy/SimilarityDetection) repository):

```bash
cd app/similarity
git submodule init
git submodule update
cd ../../
```

Create a python virtual environment and install the required packages:

```bash
python3.9 -m venv venv
. venv/bin/activate
pip install -r requirements.txt # remove +cu116 on osx
```

You can now run the API worker:

```bash
./venv/bin/dramatiq app.main -p 1 -t 1
```

And the server:

```bash
./venv/bin/flask --app app.main run --debug
```

## Production

### Deploy

Copy the file `.env.template` to a file `.env.prod`. Change it to `TARGET=prod`, and indicate the appropriate credentials.

Install docker and the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) following NVIDIA's instructions (this will be needed for the docker to use the GPU).

Modify the directory and user binding in `docker.sh` to ensure it is correct.

Build the docker using the premade script:

```bash
bash docker.sh rebuild
```

It should have started the docker, check it is the case with `sudo docker logs demowebsiteapi -f`.

The API is now accessible locally at `http://localhost:8001`. Configure a connection between the frontend and this machine (for instance using [spiped](https://www.tarsnap.com/spiped.html) or a ssh tunnel) for it to be able to access the API.

### Update

Just run:

```bash
bash docker.sh pull
```

**Note:** as a redis server is encapsulated inside the docker, its data is **non-persistent**: any task scheduled before a `bash docker.sh <anything>` will be forgotten. Result files are kept, though, as they are in the persistent storage.

*Note 2:* Docker won't be able to access the host's `http://localhost:8000/` easily, so it is not advised to use the Docker build to develop if that's the only way to access the frontend.