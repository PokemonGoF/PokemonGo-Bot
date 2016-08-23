FROM python:2.7.12-alpine

RUN apk add --update --no-cache alpine-sdk wget git\
  && rm -rf /var/cache/apk/*

WORKDIR /usr/src/app
VOLUME ["/usr/src/app/configs", "/usr/src/app/web"]

ARG timezone=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN cd /tmp && wget http://pgoapi.com/pgoencrypt.tar.gz \
    && tar zxvf pgoencrypt.tar.gz \
    && cd pgoencrypt/src \
    && make \
    && cp libencrypt.so /usr/src/app/encrypt.so \
    && cd /tmp \
    && rm -rf /tmp/pgoencrypt*

ENV LD_LIBRARY_PATH /usr/src/app

COPY requirements.txt /usr/src/app/
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN apk del alpine-sdk

ENTRYPOINT ["python", "pokecli.py"]
