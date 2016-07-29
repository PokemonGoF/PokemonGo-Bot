FROM python:2.7-onbuild

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
