FROM python:2.7-onbuild

RUN apt-get update \
    && apt-get install -y python-protobuf

VOLUME ["/usr/src/app/web"]

ENTRYPOINT ["python", "pokecli.py"]