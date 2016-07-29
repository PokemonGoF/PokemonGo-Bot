FROM python:2.7-onbuild

ARG timezone=Etc/UTC
RUN echo $timezone > /etc/timezone \
    && ln -sfn /usr/share/zoneinfo/$timezone /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update \
    && apt-get install -y python-protobuf

VOLUME ["/usr/src/app/web"]

ENTRYPOINT ["python", "pokecli.py"]