FROM python:2.7-onbuild

ARG timezone=Etc/UTC
RUN echo $timezone > /etc/timezone \
    && ln -sfn /usr/share/zoneinfo/$timezone /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
