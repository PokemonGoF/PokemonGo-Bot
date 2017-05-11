# Install the bot
## Table of Contents
- [Linux or Mac Automatic Installation](#linuxmac)
- [Windows Automatic Installation](#windows)
- [Docker Automatic Installation](#docker)


# Linux/Mac
### Requirements (click each one for install guide)
- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)
- [hashing key](http://hashing.pogodev.org) - if you want use latest API, not the old, 0.45

### Easy installation
1. Clone the git: `git clone https://github.com/PokemonGoF/PokemonGo-Bot`
2. Go into the new directory: `cd PokemonGo-Bot`
3. Run `./setup.sh -i`  
    This will install the bot and all stuff that is needed to run it (follow the steps in this process)
4. Run `./run.sh`  
    After you are done following it this will start your bot.

### To update the bot
1. Stop the bot if it's running. (use control + c twice to stop it)
2. Run `./setup.sh -r`  
    This will reset and makes sure you have no changes made to any code since it will overide it
3. Rerun the bot `./run.sh`

for manual installation please refer to [here](https://github.com/PokemonGoF/PokemonGo-Bot/blob/dev/docs/manual_installation.md)

# Windows
We do recommend Windows users to use [Docker](#docker) this will work much easier and smoother (also safer)

## Requirements
- [hashing key](http://hashing.pogodev.org) - if you want use latest API, not the old, 0.45

### Easy Installation
1. Download [PokemonGo-Bot-Install.bat](https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/windows_bat/PokemonGo-Bot-Install.bat)
2. Run `PokemonGo-Bot-install.bat`.
After that has been done the bot will be installed.
3. Run `PokemonGo-Bot-Configurator` to create auth.json, config.json and userdata.js.
4. Run `PokemonGo-Bot-Start.bat`.
This will start the bot and the web interface.

### To update the bot
1. Run `PokemonGo-Bot-Start.bat`
This will check for an update and will start the bot afterwards.

# Docker

### Easy installation
Start by downloading for your platform:
- [Mac](https://www.docker.com/products/docker#/mac)
- [Windows](https://www.docker.com/products/docker#/windows)
- [Linux](https://www.docker.com/products/docker#/linux)

Once you have Docker installed, simply create the various config files for your different accounts (e.g. `configs/config.json`, `configs/userdata.js`) and then create a Docker image for PokemonGo-Bot using the Dockerfile in this repo.

```
cd PokemonGo-Bot
docker build -t pokemongo-bot .
```

By default our Dockerfile ensures that the "master" branch will be used for building the docker container, if you want to use the "dev" branch then you should build the container with below build command:

```
docker build --build-arg BUILD_BRANCH=dev -t pokemongo-bot .
```



After build process you can verify that the image was created with:

```
docker images
```

To run the bot container with the PokemonGo-Bot Docker image you've created:

```
docker run --name=bot1-pokego --rm -it -v $(pwd)/configs/config.json:/usr/src/app/configs/config.json pokemongo-bot
```

Optionally you can set your timezone with the -e option (default is Etc/UTC). You can find an exhaustive list of timezone here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

```
docker run --name=bot1-pokego --rm -it -e TZ=Asia/Taipei -v $(pwd)/configs/config.json:/usr/src/app/configs/config.json pokemongo-bot
```

>In the case you configured authentification to be handled by auth.json file make sure you mount that file as a volume also

>```
docker run --name=bot1-pokego --rm -it -v $(pwd)/configs/auth.json:/usr/src/app/configs/auth.json  -v $(pwd)/configs/config.json:/usr/src/app/configs/config.json -v $(pwd)/web/:/usr/src/app/web/ pokemongo-bot
```

>or for a simplified version mount your whole configs/ subdir to /usr/src/app/configs

>```
docker run --name=bot1-pokego --rm -it -v $(pwd)/configs:/usr/src/app/configs -v $(pwd)/web/:/usr/src/app/web/ pokemongo-bot
```
>

Run a second container provided with the OpenPoGoBotWeb view:

```
docker run --name=bot1-pokegoweb --rm -it --volumes-from bot1-pokego -p 8000:8000 -v $(pwd)/configs/userdata.js:/usr/src/app/web/config/userdata.js -w /usr/src/app/web python:2.7 python -m SimpleHTTPServer
```
The OpenPoGoWeb will be served on `http://<your host>:8000`

### Using proxy with docker:

- https proxy
 ```
 docker run --name=bot1-pokego -e "https_proxy=https://PROXY_IP:PORT" --rm -it -v $(pwd)/configs:/usr/src/app/configs -v $(pwd)/web/:/usr/src/app/web/ pokemongocc-bot
```
- http proxy
 ```
 docker run --name=bot1-pokego -e "http_proxy=http://PROXY_IP:PORT" --rm -it -v $(pwd)/configs:/usr/src/app/configs -v $(pwd)/web/:/usr/src/app/web/ pokemongo-bot
 ```

### Remarks for Windows

Even if the previous command are valid, you will not be able to visualize the web view under Windows. 
To visualize the web view, execute instead the following commands (*make sure you are in the root folder and that your docker images is built*):

- Run the bot container:

```
docker run --name=bot1-pokego --rm -it -v $(pwd)/configs/config.json:/usr/src/app/configs/config.json -v $(pwd)/web/:/usr/src/app/web/ pokemongo-bot
```

- Run the web container:

```
docker run --name=bot1-pokegoweb --rm -it --volumes-from bot1-pokego -p 8000:8000 -v $(pwd)/configs/userdata.js:/usr/src/app/web/config/userdata.js -w /usr/src/app/web python:2.7 python -m SimpleHTTPServer
```

- Retrieve your host address:

```
  docker-machine ip default
```


Then, with your containers running and your host address, you can access the web view in your browser:

`http://<your host address>:8000 (eg http://192.168.99.100:8000)`
```
#### Errors

- An error occurred trying to connect:

Make sure your virtual machine is started, and your environment variables are set in your shell:

```
docker-machine start default
docker-machine env default
```

- Unable to find image 'pokemongo-bot:latest' locally:

Make sure that the name of the image is correct.

### Using Docker compose

if docker-compose [installed](https://docs.docker.com/compose/install/) you can alternatively run the PokemonGo-Bot ecosystem with one simple command:  
(by using the docker-compose.yml configuration in this repo)

```
docker-compose up
```

An example of routing the bot's traffic through a tor proxy can be found within the docker-compose_tor.yml file. To use a different file, supply the file name to docker-compose. The d flag is used to run this in detached mode as the tor logs overwhelm any bot logs you might wish to view. The bot logs can still be seen through `docker logs` command.

```
docker-compose -f docker-compose_tor.yml up -d 
```

Also run one single service from the compose configuration is possible:

```
docker-compose run --rm bot1-pokego
```



command to stop and remove all stopped containers: `docker-compose down`

TODO: Add infos / configuration for running multiple bot instances.

Do not push your image to a registry with your config.json and account details in it!

### Bug reporting when using docker:

Please include output of below command:
```
docker inspect --format='{{.Created}} {{.ContainerConfig.Labels}}' container_tag_or_id
```
container_tag_or_id being the final tag_id of container or the id of the intermediary layer at which the docker build failed.
