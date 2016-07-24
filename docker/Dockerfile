FROM alpine:3.4
MAINTAINER Moises Vega <moisesvega@users.noreply.github.com>

# Install  dependencies
RUN apk add --update --no-cache \
    ca-certificates \
    && update-ca-certificates \
    && apk add --update --no-cache \
      git \
      python \
      python-dev \
      py-pip \
      build-base \
      protobuf \
    && pip install --upgrade pip

# Clone repo dev branch
RUN mkdir /app
RUN git clone -b dev https://github.com/PokemonGoF/PokemonGo-Bot app/
RUN cd app && pip install -r requirements.txt

VOLUME /app
WORKDIR app/

ENTRYPOINT ["sh", "run.sh"]
