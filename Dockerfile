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
# docker build --build-arg BUILD_REPO=YourFork/PokemonGo-Bot --build-arg BUILD_BRANCH=6a4580f .

FROM alpine

ARG BUILD_REPO=PokemonGoF/PokemonGo-Bot
ARG BUILD_BRANCH=master

LABEL build_repo=$BUILD_REPO build_branch=$BUILD_BRANCH

WORKDIR /usr/src/app
VOLUME ["/usr/src/app/configs", "/usr/src/app/web"]

RUN apk -U --no-cache add python py-pip tzdata \
    && rm -rf /var/cache/apk/* \
    && find / -name '*.pyc' -o -name '*.pyo' | xargs -rn1 rm -f

ADD http://pgoapi.com/pgoencrypt.tar.gz /tmp/pgoencrypt.tar.gz
ADD https://raw.githubusercontent.com/$BUILD_REPO/$BUILD_BRANCH/requirements.txt .
RUN apk -U --no-cache add --virtual .build-dependencies python-dev gcc make musl-dev git \
    && tar zxf /tmp/pgoencrypt.tar.gz -C /tmp \
    && make -C /tmp/pgoencrypt/src \
    && cp /tmp/pgoencrypt/src/libencrypt.so /usr/src/app/encrypt.so \
    && ln -s locale.h /usr/include/xlocale.h \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-dependencies \
    && rm -rf /var/cache/apk/* /tmp/pgoencrypt* /usr/include/xlocale.h \
    && find / -name '*.pyc' -o -name '*.pyo' | xargs -rn1 rm -f

ADD https://api.github.com/repos/$BUILD_REPO/commits/$BUILD_BRANCH /tmp/pgobot-version
RUN apk -U --no-cache add --virtual .pgobot-dependencies wget ca-certificates tar jq \
    && wget -q -O- https://github.com/$BUILD_REPO/archive/$BUILD_BRANCH.tar.gz | tar zxf - --strip-components=1 -C /usr/src/app \
    && jq -r .sha /tmp/pgobot-version > /usr/src/app/version \
    && apk del .pgobot-dependencies \
    && rm -rf /var/cache/apk/* /tmp/pgobot-version

ENTRYPOINT ["python", "pokecli.py"]
