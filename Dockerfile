# To build a docker container for the "master" branch (this is the default) execute:
#
# docker build --build-arg BUILD_BRANCH=master .
# (or)
# docker build .
#
# To build a docker container for the "dev" branch execute:
# 
# docker build --build-arg BUILD_BRANCH=dev .
# 
# You can also build from different fork and specify a particular commit as the branch
# 
# docker build  --build-arg BUILD_REPO=YourFork/PokemonGo-Bot --build-arg BUILD_BRANCH=6a4580f .

FROM alpine

ARG BUILD_REPO=PokemonGoF/PokemonGo-Bot
ARG BUILD_BRANCH=master
ARG TIMEZONE=Etc/UTC

LABEL build_repo=$BUILD_REPO build_branch=$BUILD_BRANCH

WORKDIR /usr/src/app
VOLUME ["/usr/src/app/configs", "/usr/src/app/web"]

ADD https://raw.githubusercontent.com/$BUILD_REPO/$BUILD_BRANCH/requirements.txt .
RUN apk -U --no-cache add python py-pip \
    && apk --no-cache add --virtual .build-dependencies python-dev gcc make musl-dev git tzdata tar \
    && cp -fa /usr/share/zoneinfo/$TIMEZONE /etc/localtime \
    && echo $TIMEZONE > /etc/timezone \
    && ln -s locale.h /usr/include/xlocale.h \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-dependencies \
    && rm -rf /var/cache/apk/* /usr/include/xlocale.h \
    && find / -name '*.pyc' -o -name '*.pyo' -exec rm -f {} \;

ADD http://pgoapi.com/pgoencrypt.tar.gz /tmp/pgoencrypt.tar.gz
RUN apk --no-cache add --virtual .pgoencrypt-dependencies gcc make musl-dev tar \
    && cat /tmp/pgoencrypt.tar.gz | tar xzf - -C /tmp \
    && make -C /tmp/pgoencrypt/src \
    && cp /tmp/pgoencrypt/src/libencrypt.so /usr/src/app/encrypt.so \
    && apk del .pgoencrypt-dependencies \
    && rm -rf /var/cache/apk/* /tmp/pgoencrypt /tmp/pgoencrypt.tar.gz

ADD https://github.com/$BUILD_REPO/archive/$BUILD_BRANCH.tar.gz /tmp
RUN apk -U --no-cache add --virtual .tar-deps tar \
    && cat /tmp/$BUILD_BRANCH.tar.gz | tar -zxf - --strip-components=1 -C /usr/src/app \
    && apk del .tar-deps \
    && rm /tmp/$BUILD_BRANCH.tar.gz

ENTRYPOINT ["python", "pokecli.py"]
