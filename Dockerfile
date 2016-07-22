FROM gliderlabs/alpine:3.4

COPY requirements.txt /app/
WORKDIR /app/

RUN apk add --update --no-cache \
  ca-certificates \
  && update-ca-certificates \
  && apk add --update --no-cache \
    git \
    python \
    python-dev \
    py-pip \
    build-base \
  && pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del git

COPY . /app

ENTRYPOINT ["/usr/bin/python", "pokecli.py"]
