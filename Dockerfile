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

FROM python:2.7.12-alpine

RUN apk add --update --no-cache alpine-sdk git

ARG BUILD_BRANCH
ENV BUILD_BRANCH ${BUILD_BRANCH:-master}

ARG BUILD_REPO
ENV BUILD_REPO ${BUILD_REPO:-PokemonGoF/PokemonGo-Bot}

LABEL build_repo=$BUILD_REPO build_branch=$BUILD_BRANCH

ADD https://github.com/$BUILD_REPO/archive/$BUILD_BRANCH.tar.gz .
RUN tar -zxvf $BUILD_BRANCH.tar.gz && mv PokemonGo-Bot-* /usr/src/app && rm $BUILD_BRANCH.tar.gz

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
