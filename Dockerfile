FROM python:2.7-onbuild

ARG timezone=Etc/UTC
RUN echo $timezone > /etc/timezone \
    && ln -sfn /usr/share/zoneinfo/$timezone /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update \
    && apt-get install -y python-protobuf
RUN cd /tmp && wget "http://pgoapi.com/pgoencrypt.tar.gz" \
    && tar zxvf pgoencrypt.tar.gz \
    && cd pgoencrypt/src \
    && make \
    && cp libencrypt.so /usr/src/app/encrypt.so \
    && cd /tmp \
    && rm -rf /tmp/pgoencrypt*

VOLUME ["/usr/src/app/web"]

ENV LD_LIBRARY_PATH /usr/src/app

ENTRYPOINT ["python", "pokecli.py"]
