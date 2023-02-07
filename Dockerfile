# Docker image for barcode-server

# dont use alpine for python builds: https://pythonspeed.com/articles/alpine-docker-python/
FROM python:3.11-slim-buster

WORKDIR /app

COPY . .

RUN apt-get update \
    && apt-get -y install sudo python3-pip python3-evdev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip;\
    pip3 install evdev;\
    pip install pipenv;\
    PIP_IGNORE_INSTALLED=1 pipenv install --system --deploy;\
    pip install .

ENV PUID=1000 PGID=1000

ENTRYPOINT [ "docker/entrypoint.sh", "barcode-server" ]
CMD [ "run" ]
