FROM gliderlabs/alpine:3.4

# common library
RUN apk add --update --no-cache \
  ca-certificates \
  && update-ca-certificates \
  && apk add --update --no-cache \
    git \
    python \
    python-dev \
    py-pip \
    build-base \
  && pip install --upgrade pip


COPY requirements.txt /app/
WORKDIR /app/

# keep pip on other layer
RUN pip install --no-cache-dir -r requirements.txt \
  && apk del git

COPY . /app

ENTRYPOINT ["/usr/bin/python", "pokecli.py"]
