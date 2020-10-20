# Docker image for barcode-server

FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install --upgrade pip;\
    pip install pipenv;\
    pipenv install --system --deploy

CMD [ "python", "./barcode_server/main.py" ]
