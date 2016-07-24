FROM python:2.7-alpine

#important for building git tejado pgoapi dependencies.
RUN apk add --no-cache git build-base

#stuff for build app
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/

RUN apk add --no-cache git build-base && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del git build-base

COPY . /usr/src/app
ONBUILD COPY ./config.json /usr/src/app
ONBUILD COPY ./release_config.json /usr/src/app

# -u parameter for unbuffer system output and see it in logs.
ENTRYPOINT ["python", "-u", "pokecli.py", "-cf", "config.json"]

