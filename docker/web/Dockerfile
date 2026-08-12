# 1st build: compile svelte files
FROM node:23 AS svelte_build

WORKDIR /app
COPY front .
WORKDIR /app/interface/
RUN npm install
RUN npm run build

# --------------------------------------------
# Final image
FROM ubuntu:22.04

# Use args passed in the build command and retrieved from docker/.env
ARG USERID
ARG PORT

ENV USER=aikondemo
ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/home/${USER}
ENV UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_CACHE_DIR=/home/${USER}/.uv_cache
ENV UV_PROJECT_ENVIRONMENT=/home/${USER}/app/.venv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
ENV N_PROCESS=50

# Set up environment
ENV TERM=linux
SHELL ["/bin/bash", "-c"]
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    zip \
    curl \
    ca-certificates \
    # NOTE why ? docker-compose aldready has a redis
    redis-server \
    supervisor \
    tzdata \
    ffmpeg \
    libsm6 \
    libxext6 \
    libpq-dev \
    vim \
    build-essential \
    poppler-utils \
    ghostscript

# install UV. https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd -u ${USERID} -m -d /home/${USER} ${USER}

# install UV. https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd -u ${USERID} -m -d /home/${USER} ${USER}

WORKDIR /home/${USER}

# Copy app files
COPY --chown=${USER} front /home/${USER}/app
COPY --chown=${USER} docker/supervisord.conf /home/${USER}/supervisord.conf

WORKDIR /home/${USER}/app

# Install UV/python dependencies
RUN uv python install 3.11
RUN uv sync --locked --group=prod

# TODO less aggrssive permissions ?
# Set permissions on UV and NPM directories
# xargs is used to run chmod in parrallel in up to ${N_PROCESS} processes
RUN find ${UV_CACHE_DIR} -print0 | xargs -0 -P ${N_PROCESS} chown ${USER}:${USER}
# to speed up even more, we run the 3 chowns in parrallel and parrallelize each command using xargs
RUN \
    find ${UV_CACHE_DIR} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rwxXst & \
    find ${UV_PROJECT_ENVIRONMENT} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rX & \
    find ${UV_PYTHON_INSTALL_DIR} -print0 | xargs -0 -P ${N_PROCESS} chmod a+rX & \
    wait

# Must match the PORT in docker.sh
EXPOSE ${PORT}

RUN mkdir -p /home/${USER}/app/staticfiles && chown ${USER}:${USER} /home/${USER}/app/staticfiles
COPY --from=svelte_build --chown=${USER}:${USER} /app/shared/static/dist/ /home/${USER}/app/shared/static/dist/

COPY --chown=${USER} docker/manage.sh /home/${USER}/manage.sh
RUN chmod +x /home/${USER}/manage.sh

# Launch app
CMD /home/${USER}/manage.sh && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && \
    supervisord -c /home/${USER}/supervisord.conf
