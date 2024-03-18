# API

This folder contains the code for the worker API.

## Development

Copy the file `.env.template` to a file `.env`. Change its content to match your setup (especially regarding the paths).

You need to install redis and python:

```bash
sudo apt-get install redis-server python3-venv python3-dev
```

[//]: # (Configure Redis)
[//]: # (```bash)
[//]: # (# Find config file)
[//]: # (sudo find / -name redis.)
[//]: # (vi <path/to/redis.conf>)
[//]: # (```)
[//]: # (Find &#40;`/` command then type `requirepass`&#41; and modify directive &#40;uncomment and set password&#41;:)
[//]: # (```bash)
[//]: # (requirepass <redis_password>)
[//]: # (```)

You need to init the dti submodule (and have the access to the [dti-sprites](https://github.com/sonatbaltaci/dti-sprites) project):

```bash
git submodule init
git submodule update

# once initiate, update the submodule code with
git submodule update --remote
```

Create a python virtual environment and install the required packages:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
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

Requirements:
- Docker
- Python 3.10

Clone and init submodule

```shell
git clone git@github.com:Evarin/DTI-demo.git
cd api/

git submodule init
git submodule update
```

Install docker and the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) following NVIDIA's instructions (this will be needed for the docker to use the GPU).

Copy the file `.env` to a file `.env.prod`. Change it to `TARGET=prod`, and indicate the appropriate credentials.

```shell
cp .env.template .env.prod
sed -i '' -e "s~^TARGET=.*~TARGET=\"prod\"~" .env.prod
```

Add the user to Docker group
```bash
sudo usermod -aG docker $USER
su - ${USER} # Reload session for the action to take effect
```

In [`docker.sh`](docker.sh), modify the variables depending on your setup:
- `DATA_FOLDER`: absolute path to directory where results are stored
- `DEMO_UID`: Universally Unique Identifier of the user that execute Dockerfile (`id -u <username>`)
- `DEVICE_NB`: GPU number


Build the docker using the premade script:

```bash
bash docker.sh rebuild
```

It should have started the docker, check it is the case with:
- `docker logs demowebsiteapi --tail 50`: show last 50 log messages
- `docker ps` show running docker containers

The API is now accessible locally at `http://localhost:8001`.

#### Secure connection

A good thing is to tunnel securely the connection between API and front. For `discover-demo.enpc.fr`, it is done with `spiped`, based on [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-encrypt-traffic-to-redis-with-spiped-on-ubuntu-16-04)
(with target ports 8001, in service `spiped-connect` on frontend server and `spiped-dti` on worker).

```bash
sudo apt-get update
sudo apt-get install spiped # install spiped
sudo mkdir /etc/spiped
sudo dd if=/dev/urandom of=/etc/spiped/dti.key bs=32 count=1
sudo chmod 644 /etc/spiped/dti.key
```

Create service config file for spiped (`sudo vi /etc/systemd/system/spiped-dti.service`)
Get `<docker-ip>` with `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' demowebsiteapi` or use `127.0.0.1`

```bash
[Unit]
Description=Spiped connection for docker container
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=300

[Service]
ExecStart=/usr/bin/spiped -F -d -s [0.0.0.0]:8080 -t [<docker-ip>]:8001 -k /etc/spiped/dti.key
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl start spiped-dti.service
sudo systemctl enable spiped-dti.service
```

Transfer key to front
```bash
scp <gpu-host>:/etc/spiped/dti.key ~
sudo chmod 644 ~/dti.key
scp ~/dti.key <front-host>:.
ssh <front-host>
sudo mkdir /etc/spiped
sudo cp dti.key /etc/spiped/
sudo chmod 644 /etc/spiped/dti.key
```

Create service config file for spiped on front machine (`sudo vi /etc/systemd/system/spiped-connect.service`)
Get `<gpu-ip>` with `hostname -I` on the machine where is deployed the API

```bash
[Unit]
Description=Spiped connection to API
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=300

[Service]
ExecStart=/usr/bin/spiped -F -e -s [127.0.0.1]:8001 -t [<gpu-ip>]:8080 -k /etc/spiped/dti.key
Restart=Always

[Install]
WantedBy=multi-user.target
```

Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl start spiped-connect.service
sudo systemctl enable spiped-connect.service
```

### Update

Just run:

```bash
bash docker.sh pull
```

**Note:** as a redis server is encapsulated inside the docker, its data is **non-persistent**: any task scheduled before a `bash docker.sh <anything>` will be forgotten. Result files are kept, though, as they are in the persistent storage.

*Note 2:* Docker won't be able to access the host's `http://localhost:8000/` easily, so it is not advised to use the Docker build to develop if that's the only way to access the frontend.
