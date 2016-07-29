FROM python:2.7-onbuild

RUN apt-get update \
    && apt-get install -y python-protobuf

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
