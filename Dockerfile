# Docker image for barcode-server
# dont use alpine for python builds: https://pythonspeed.com/articles/alpine-docker-python/
FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION="1.4.1"
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV VENV_HOME=/opt/poetry
WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN apt-get update \
 && apt-get -y install sudo python3-pip python3-evdev \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv ${VENV_HOME} \
 && ${VENV_HOME}/bin/pip install --upgrade pip \
 && ${VENV_HOME}/bin/pip install "poetry==${POETRY_VERSION}" \
 && ${VENV_HOME}/bin/poetry check \
 && POETRY_VIRTUALENVS_CREATE=false ${VENV_HOME}/bin/poetry install --no-interaction --no-cache --only main \
 && ${VENV_HOME}/bin/pip uninstall -y poetry

# Add Poetry to PATH
ENV PATH="${VENV_HOME}/bin:${PATH}"

COPY docker docker
COPY barcode_server barcode_server
COPY README.md README.md

RUN ${VENV_HOME}/bin/pip install .

ENV PUID=1000 PGID=1000

ENTRYPOINT "docker/entrypoint.sh" "${VENV_HOME}/bin/barcode-server" "$0" "$@"
CMD [ "run" ]
