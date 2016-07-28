<p align="center">
  <a href="">
    <img alt="Logo" src="https://www.brooklinelibrary.org/wp-content/uploads/2016/07/2000px-Pok%C3%A9_Ball.svg_-1.png" width="100">
  </a>
</p>

<p align="center">
  <a href="https://pokemongo-bot.herokuapp.com/"><img alt="Slack" src="https://pokemongo-bot.herokuapp.com/badge.svg"></a>
</p>

# PokemonGo-Bot
The Pokemon Go Bot, baking with community.
## Help Needed on [Desktop Version](https://github.com/PokemonGoF/PokemonGo-Bot-Desktop)
## Project Chat
We use [Slack](https://slack.com) as a web chat. [Click here to join the chat!](https://pokemongo-bot.herokuapp.com)
## Breaking Changes
You need modify config.json (config.json.example for example) then pokecli.py --config config.json
Please clean up your old clone if you have issue, and following the [install instruction](https://github.com/PokemonGoF/PokemonGo-Bot#installation).

## About dev/master Branch
Dev branch has the most up-to-date features, but be aware that there might be some broken changes. Your contribution and PR for fixes are warm welcome.
Master branch is the stable branch.
No PR on master branch to keep things easier.
## Table of Contents
- [Project Chat](#project-chat)
- [Features](#features)
- [TODO List](#todo-list)
- __Installation__
  - [Requirements](#requirements)
  - [Mac](#installation-mac)
  - [Linux](#installation-linux)
  - [Windows](#installation-windows)
- [Develop PokemonGo-Bot](develop-pokemonGo-bot)
- [Usage](#usage)
- [Docker Usage](#how-to-run-with-docker)
- [FAQ](#faq)
- [Credits](#credits)
- [Donation](#donation)

## Features
 * Search Fort (Spin Pokestop)
 * Catch Pokemon
 * Release low cp pokemon
 * Walking as you
 * Limit the step to farm specific area for pokestops
 * Use the ball you have to catch, don't if you don't have
 * Rudimentary IV Functionality filter
 * Auto switch mode (Full of item then catch, no ball useable then farm)
 * Ignore certain pokemon filter
 * Use superior ball types when necessary
 * When out of normal pokeballs, use the next type of ball unless there are less than 10 of that type, in which case switch to farm mode
 * Drop items when bag is full (In Testing, Document contribute needed)
 * Pokemon catch filter (In Testing, Document contribute needed)
 * Google Map API key setup (Readme update needed)
 * Show all objects on map (In Testing)
 * Evolve pokemons (Code in, Need input, In Testing)

## TODO List

- [ ] Standalone Desktop APP
- [ ] Pokemon transfer filter ?? This already done, right?
- [ ] Hatch eggs
- [ ] Incubate eggs
- [ ] Use candy

## Gym Battles
This bot takes a strong stance against automating gym battles. Botting gyms will have a negative effect on most players and thus the game as a whole. We will thus never accept contributions or changes containing code specific for gym battles.

## Installation

### Requirements (click each one for install guide)

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)
- [docker](https://docs.docker.com/engine/installation/) (Optional)
- [protobuf 3](https://github.com/google/protobuf) (OS Dependent, see below)

### Note on virtualenv
We recommend you use virtualenv, not only will this tool keep your OS clean from all the python plugins.
It also provide an virtual space for more than 1 instance!

### Protobuf 3 installation

- OS X:  `brew update && brew install --devel protobuf`
- Windows: Download protobuf 3.0: [here](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip) and unzip `bin/protoc.exe` into a folder in your PATH.
- Linux: `sudo apt-get install python-protobuf`

### Note on branch
Please keep in mind that master is not always up-to-date whereas 'dev' is. In the installation note below change `master` to `dev` if you want to get and use the latest version.

### Installation Linux
(change master to dev for the latest version)

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot
$ cd PokemonGo-Bot
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Installation Mac
(change master to dev for the latest version)

Make sure you install the following first:
[Requirements](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation)

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot
$ cd PokemonGo-Bot
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Installation Windows
(change master to dev for the latest version)

On Windows, you will need to install PyYaml through the installer and not through requirements.txt.

##### Windows vista, 7, 8:
Go to : http://pyyaml.org/wiki/PyYAML , download the right version for your pc and install it

##### Windows 10:
Go to [this](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml) page and download: PyYAML-3.11-cp27-cp27m-win32.whl
(If running 64-bit python or if you get a 'not a supported wheel on this platform' error,
download the 64 bit version instead: PyYAML-3.11-cp27-cp27m-win_amd64.whl )

```
$ cd download-directory
$ pip install PyYAML-3.11-cp27-cp27m-win32.whl
// if you needed to download the 64-bit version)
// (replace PyYAML-3.11-cp27-cp27m-win32.whl with PyYAML-3.11-cp27-cp27m-win_amd64.whl
```

After this, just do:

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot
$ cd PokemonGo-Bot
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Develop PokemonGo-Bot

```
$ git clone -b dev https://github.com/PokemonGoF/PokemonGo-Bot
$ cd PokemonGo-Bot
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Google Maps API (in development)

Google Maps API: a brief guide to your own key

This project uses Google Maps. There's one map coupled with the project, but as it gets more popular we'll definitely hit the rate-limit making the map unusable. That said, here's how you can get your own and replace ours:

1. Navigate to this [page](https://console.developers.google.com/flows/enableapi?apiid=maps_backend,geocoding_backend,directions_backend,distance_matrix_backend,elevation_backend,places_backend&keyType=CLIENT_SIDE&reusekey=true)
2. Select 'Create a project' in the dropdown menu.
3. Wait an eternity.
4. Click 'Create' on the next page (optionally, fill out the info)
5. Copy the API key that appears.
6. After the code done, will update here how to replace.

### Python possible bug
If you encounter problems with the module `ssl` and it's function `_create_unverified_context`, just comment it. (Solution available in Python 2.7.11)
In order to comment out the function and the module, please follow the instructions below:
- edit `pokecli.py`
- put `#` before `if` (line 43) and `ssl` (line 44)
- save it

Please keep in mind that this fix is only necessary if your python version don't have the `_create_unverified_context` argument in the ssl module.

## Update
To update your project do: `git pull` in the project folder

## Usage (up-to-date)
	1/ copy `config.json.example` to `config.json` and `release_config.json.example` to `release_config.json`.
	2/ Edit `config.json` and replace `auth_service`, `username`, `password`, `location` and `gmapkey` with your parameters (other keys are optional, check `Advance Configuration` below)

## Advance Configuration
- `max_steps` :
- `mode` :
- `walk` :
- `debug` : Let the default value here except if you are developper
- `test` : Let the default value here except if you are developper
- `initial_transfer` : Set this to 1 if you want to transfer pokemon
- `location_cache` :
- `distance_unit` :
- `item_filter` :
- `evolve_all` : Set to true to evolve pokemons if possible

### Evolve All Configuration
    By setting the `evolve_all` attribute in config.json, you can instruct the bot to automatically
    evolve specified pokemons on startup. This is especially useful for batch-evolving after popping up
    a lucky egg (currently this needs to be done manually).

    The evolve all mechanism evolves only higher CP pokemons. It does this by first ordering them from high-to-low CP.
    It will also automatically transfer the evolved pokemons based on the release configuration.

    Examples on how to use (set in config.json):

    1. "evolve_all": "all"
      Will evolve ALL pokemons.
    2. "evolve_all": "Pidgey,Weedle"
      Will only evolve Pidgey and Weedle.
    3. Not setting evolve_all or having any other string would not evolve any pokemons on startup.

## How to run with Docker

## How to add/discover new API
  The example is [here](https://github.com/PokemonGoF/PokemonGo-Bot/commit/46e2352ce9f349cc127a408959679282f9999585)
    1. Check the type of your API request in   [POGOProtos](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/RequestType.proto) For example: RECYCLE_INVENTORY_ITEM
    2. Convert to the api call in pokemongo_bot/__init__.py,  RECYCLE_INVENTORY_ITEM change to self.api.recycle_inventory_item
        ```
        def drop_item(self,item_id,count):
            self.api.recycle_inventory_item(...............)
        ```
    3. Where is the param list?
        You need check this [Requests/Messages/RecycleInventoryItemMessage.proto](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/Messages/RecycleInventoryItemMessage.proto)
    4. Then our final api call is
        ```
        def drop_item(self,item_id,count):
            self.api.recycle_inventory_item(item_id=item_id,count=count)
            inventory_req = self.api.call()
            print(inventory_req)
        ```
    5. You can now debug on the log to see if get what you need

## How to set up a simple webserver with nginx
### Nginx on Ubuntu 14.x, 16.x
#### 1. Install nginx on your Ubuntu machine (e.g. on locally or AWS)
```
sudo apt-get update
sudo apt-get install nginx
```

#### 2. Check the webserver
Check if the webserver is running by using your browser and entering the IP address of your local machine/server.
On a local machine this would be http://127.0.0.1. On AWS this is your public DNS if you havent configured an elastic IP.

#### 3. Change Base Directory of the Webserver
```
sudo nano "/etc/nginx/sites-enabled/default"
```
Comment out following line: ```root /var/www/html;``` and change it to the web folder of your PokemonGo-Bot: eg:
```
/home/user/dev/PokemonGo-Bot/web;
```

## FAQ

### What's IV ?
Here's the [introduction](http://bulbapedia.bulbagarden.net/wiki/Individual_values)

### Does it run automatally?
Not yet, still need a trainer to train the script param. But we are very close to.
### Set GEO Location
It works, use -l "xx.yyyy,zz.ttttt" to set lat long for location. -- diordache
### Google login issues (Login Error, Server busy)?

Try to generate an [app password](!https://support.google.com/accounts/answer/185833?hl=en) and set is as
```
-p "<your-app-password>"
```
This error mostly occurs for those who are using 2 factor authentication, but either way, for the purpose of security it would be nice to have a separate password for the bot app.


### FLEE
The status code "3" corresponds to "Flee" - meaning your Pokemon has ran away.
   {"responses": { "CATCH_POKEMON": { "status": 3 } }
### My pokemon are not showing up in my Pokedex?
Finish the tutorial on a smartphone. This will then allow everything to be visible.
### How can I maximise my XP per hour?
Quick Tip: When using this script, use a Lucky egg to double the XP for 30 mins. You will level up much faster. A Lucky egg is obtained on level 9 and further on whilst leveling up. (from VipsForever via /r/pokemongodev)
### How can I not collect certain pokemon
You don't want to collect common pokemon once you hit a certain level. It will
slow down leveling but you won't fill up either.

Create the following filter
```
./data/catch-ignore.yml
```
It's a yaml file with a list of names so make it look like
```
ignore:
  - Pidgey
  - Rattata
  - Pidgeotto
  - Spearow
  - Ekans
  - Zubat
```
### How do I use the map??
You can either view the map via opening the html file, or by serving it with SimpleHTTPServer (runs on localhost:8000)
To use SimpleHTTPServer:
```$ python -m SimpleHTTPServer [port]```
The default port is 8080, you can change that by giving a port number.
Anything above port 1000 does not require root.
You will need to set your username(s) in the userdata.js file before opening:
Copy userdata.js.example to userdata.js and edit with your favorite text editor.
put your username in the quotes instead of "username"
If using multiple usernames format like this:
```var users = ["username1","username2"];```

---------
## Contributors (Don't forget add yours here when you create PR)
 * eggins -- The first pull request :)
 * crack00r
 * ethervoid
 * Bashin
 * tstumm
 * TheGoldenXY
 * Reaver01
 * rarshonsky
 * earthchie
 * haykuro
 * 05-032
 * sinistance
 * CapCap
 * mzupan
 * gnekic(GeXx)
 * Shoh
 * luizperes
 * brantje
 * VirtualSatai
 * dmateusp
 * jtdroste
 * msoedov
 * Grace
 * Calcyfer
 * asaf400
 * guyz
 * DavidK1m
 * budi-khoirudin
 * riberod07
 * th3w4y
 * Leaklessgfy

-------
## Credits
- [tejado](https://github.com/tejado) many thanks for the API
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff


## Donation

Bitcoin Address:  1PJMCx9NNQRasQYaa4MMff9yyNFffhHgLu

<p align="center">
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=WQUXDC54W6EVY"><img src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif"></a>
</p>

[![Analytics](https://ga-beacon.appspot.com/UA-81468120-1/welcome-page-master)](https://github.com/igrigorik/ga-beacon)
