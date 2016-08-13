Start by downloading for your platform: [Mac](https://www.docker.com/products/docker#/mac), [Windows](https://www.docker.com/products/docker#/windows), or [Linux](https://www.docker.com/products/docker#/linux). 

Once you have Docker installed, simply create the various config files for your different accounts (e.g. `configs/config.json`, `configs/userdata.js`) and then create a Docker image for PokemonGo-Bot using the Dockerfile in this repo.

```
cd PokemonGo-Bot
docker build --build-arg timezone=Europe/London -t pokemongo-bot .
```

Optionally you can set your timezone with the --build-arg option (default is Etc/UTC) 

After build process you can verify that the image was created with:

```
docker images
```

To run PokemonGo-Bot Docker image you've created:

```
docker run --name=bot1-pokego --rm -it -v $(pwd)/configs/config.json:/usr/src/app/configs/config.json pokemongo-bot
```

Run a second container provided with the OpenPoGoBotWeb view:

```
docker run --name=bot1-pokegoweb --rm -it --volumes-from bot1-pokego -p 8000:8000 -v $(pwd)/configs/userdata.js:/usr/src/app/web/userdata.js -w /usr/src/app/web python:2.7 python -m SimpleHTTPServer
```
The OpenPoGoWeb will be served on `http://<your host>:8000`

if docker-compose [installed](https://docs.docker.com/compose/install/) you can alternatively run the PokemonGo-Bot ecosystem with one simple command:  
(by using the docker-compose.yml configuration in this repo)

```
docker-compose up
```

Also run one single service from the compose configuration is possible:

```
docker-compose run --rm bot1-pokego
```

command for remove all stopped containers: `docker-compose rm`

TODO: Add infos / configuration for running multiple bot instances.

Do not push your image to a registry with your config.json and account details in it!
