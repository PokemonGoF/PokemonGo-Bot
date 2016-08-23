FROM python:2.7.12-alpine

RUN apk add --update --no-cache build-base gcc abuild binutils binutils-doc gcc-doc py-pip python-dev wget git\
  && pip install virtualenv \
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
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN apk del build-base gcc abuild binutils binutils-doc gcc-doc

ENTRYPOINT ["python", "pokecli.py"]
