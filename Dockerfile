FROM python:2.7.12-alpine

RUN apk add --update --no-cache alpine-sdk git

ADD https://github.com/PokemonGoF/PokemonGo-Bot/archive/dev.tar.gz .
RUN tar -zxvf dev.tar.gz && mv PokemonGo-Bot-dev /usr/src/app && rm dev.tar.gz

WORKDIR /usr/src/app
VOLUME ["/usr/src/app/configs", "/usr/src/app/web"]

ARG timezone=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#setup the bot
ADD http://pgoapi.com/pgoencrypt.tar.gz /tmp/
RUN cd /tmp && tar zxvf pgoencrypt.tar.gz \
    && cd pgoencrypt/src \
    && make \
    && cp libencrypt.so /usr/src/app/encrypt.so \
    && cd /tmp \
    && rm -rf /tmp/pgoencrypt*

ENV LD_LIBRARY_PATH /usr/src/app

RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install --no-cache-dir -r requirements.txt

#remove unused stuff
RUN apk del alpine-sdk\
  && rm -rf /var/cache/apk/*

ENTRYPOINT ["python", "pokecli.py"]
