#Install the bot
## Table of Contents
- [Linux or Mac Automatic Installation](#linuxmac)
- [Windows Automatic Installation](#windows)
- [Docker Automatic Installation](#docker)


#Linux/Mac
### Requirements (click each one for install guide)
- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)

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

for manual installation please refer to [here](https://github.com/nivong/PokemonGo-Bot/blob/dev/docs/manual_installation.md)

#Windows
We do recommend Windows users to use [Docker](#docker) this will work much easier and smoother (also saver)

##Requirements

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Protoc](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip)
- [Microsoft Visual C++ Compiler for Python 2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266)

###Easy Installation
1. Download `PokemonGo-Bot-install.bat` file from [HERE](https://raw.githubusercontent.com/nivong/PokemonGo-Bot/dev/windows%20bat/PokemonGo-Bot-Install.bat)
2. Run `PokemonGo-Bot-install.bat`
After that has done the bot will be installed
4. Run `PokemonGo-Bot-StartBot.bat`
This will start the bot itself
OPTIONAL: 5. Run `PokemonGo-Bot-StartServer.bat`
This will start the web interface and is optional stap

### To update the bot
1. Stop the bot by closing everything
2. Run `PokemonGo-Bot-Update.bat`
3. Rerun the bot by using `PokemonGo-Bot-StartBot.bat`

### To repair the bot if it isn't working for some reason
1. Stop the bot by closing everything
2. Run `PokemonGo-Bot-Repair.bat`
3. Rerun the bot by using `PokemonGo-Bot-StartBot.bat`

#Docker

###Easy installation
Start by downloading for your platform:
- [Mac](https://www.docker.com/products/docker#/mac)
- [Windows](https://www.docker.com/products/docker#/windows)
- [Linux](https://www.docker.com/products/docker#/linux)

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
