# usage:
# docker build -t pogobot
# docker run -d --name "pogobot" pogobot
FROM python:2.7-alpine

WORKDIR /usr/src/pogobot

COPY . /usr/src/pogobot

RUN apk add --no-cache build-base \
 && apk add --no-cache git \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del build-base

ENTRYPOINT ["python", "pokecli.py"]
