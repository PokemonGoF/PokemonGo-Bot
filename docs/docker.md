Start by downloading for your platform: [Mac](https://www.docker.com/products/docker#/mac), [Windows](https://www.docker.com/products/docker#/windows), or [Linux](https://www.docker.com/products/docker#/linux). Once you have Docker installed, simply create the various config.json files for your different accounts (e.g. `configs/config-account1.json`) and then create a Docker image for PokemonGo-Bot using the Dockerfile in this repo.
```
cd PokemonGo-Bot
docker build -t pokemongo-bot .
```
You can verify that the image was created with:
```
docker images
```

To run PokemonGo-Bot Docker image you've created, simple run:
```
docker run --name=pokego-bot1 --rm -it -v $(pwd)/configs/config-account1.json:/usr/src/app/configs/config.json pokemongo-bot
```
_Check the logs in real-time `docker logs -f pgobot`_

If you want to run multiple accounts with the same Docker image, simply specify different config.json and names in the Docker run command.
Do not push your image to a registry with your config.json and account details in it!

Share web folder with host:
```
docker run -it -v $(pwd)/web/:/usr/src/app/web --rm --name=pgo-bot-acct1 pokemongo-bot --config config.json
```

TODO: Add configuration for running multiple Docker containers from the same image for every bot instance, and a single container for the web UI.


Sample docker-compose.yml How to  run 3 bot with only 1 web-server

```
version: '2'
services:
  bot1-pokego:
    image: pokemongo-bot
    volumes:
      - ./configs/config.bot1name.json:/usr/src/app/configs/config.json
      - ./configs/siam.path.json:/usr/src/app/configs/path.json
      - ./data:/usr/src/app/data
      - ./web:/usr/src/app/web
    stdin_open: true
    tty: true
  bot2-pokego:
    image: pokemongo-bot
    volumes:
      - ./configs/config.bot2name.json:/usr/src/app/configs/config.json
      - ./configs/japan.path.json:/usr/src/app/configs/path.json
      - ./data:/usr/src/app/data
      - ./web:/usr/src/app/web
    stdin_open: true
    tty: true
  bot3-pokego:
    image: pokemongo-bot
    volumes:
      - ./configs/config.bot3name.json:/usr/src/app/configs/config.json
      - ./configs/LA.path.json:/usr/src/app/configs/path.json
      - ./data:/usr/src/app/data
      - ./web:/usr/src/app/web
    stdin_open: true
    tty: true
  bot1-pokegoweb:
    image: python:2.7
    ports:
     - "80:8000"
    volumes_from:
     - bot1-pokego
     - bot2-pokego
     - bot3-pokego
    volumes:
    - ./web/config/userdata.all.js:/usr/src/app/web/config/userdata.js
    working_dir: /usr/src/app/web
    command: bash -c "echo 'Serving HTTP on 0.0.0.0 port 8000' && python -m SimpleHTTPServer > /dev/null 2>&1"
    depends_on:
     - bot1-pokego
     - bot2-pokego
     - bot3-pokego

```
sample multi-account userdata at  /web/config/userdata.all.js 
`users: ["bot1name","bot2@gmail.com","bpt3name"],`

run command
docker-compose up -d 
