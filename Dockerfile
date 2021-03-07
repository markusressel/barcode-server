# Docker image for barcode-server

FROM python:3.8

WORKDIR /app

COPY . .

RUN apt-get update \
 && apt-get -y install sudo
RUN pip install --upgrade pip;\
    pip install pipenv;\
    pipenv install --system --deploy;\
    pip install .

ENV PUID=1000 PGID=1000

ENTRYPOINT [ "docker/entrypoint.sh", "barcode-server" ]
CMD [ "run" ]
