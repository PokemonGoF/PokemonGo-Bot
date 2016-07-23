<p align="center">
  <a href="">
    <img alt="Logo" src="https://www.brooklinelibrary.org/wp-content/uploads/2016/07/2000px-Pok%C3%A9_Ball.svg_-1.png" width="100">
  </a>
</p>

<p align="center">
  <a href="https://pokemongo-bot.herokuapp.com/"><img alt="Slack" src="https://pokemongo-bot.herokuapp.com/badge.svg"></a>
</p>

# PokemonGo-Bot
A python script for __catching pokemons__ and __spinning pokestops__ on PokemonGo.


## Project Chat
We use [Slack](https://slack.com) as a web chat. [Click here to join the chat!](https://pokemongo-bot.herokuapp.com)

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
 * Use the ball you have to catch, don't if you don't have
 * Rudimentary IV Functionality filter (Need verify)
 * Auto switch mode(Full of item then catch, no ball useable then farm)
 * Ignore certain pokemon filter

## TODO List

- [ ] Standalone Desktop APP
- [x] Google Map API key setup (Readme update needed)
- [ ] Show all objects on map
- [x] Limit the step to farm specific area for pokestops
- [ ] Pokemon transfer filter
- [ ] Drop items when bag is full
- [x] Pokemon catch filter
- [ ] Hatch eggs
- [ ] Incubate eggs
- [ ] Evolve pokemons
- [ ] Use candy
- [x] Code refactor

## Installation

### Requirements (click each one for install guide)

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Optional)
- [docker](https://docs.docker.com/engine/installation/) (Optional)
- [protobuf 3](https://github.com/google/protobuf) (OS Dependent, see below)

### Protobuf 3 installation

- OS X:  `brew update && brew install --devel protobuf`
- Windows: Download protobuf 3.0: [here](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip) and unzip `bin/protoc.exe` into a folder in your PATH.
- Linux: `apt-get install python-protobuf`


### Installation Linux

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
$ pip install -r requirements.txt
```

### Installation Mac

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
$ virtualenv .  
$ source bin/activate  
$ pip install -r requirements.txt
```

### Installation Windows

###### Windows Note
On Windows, you will need to install PyYaml through the  [installer](http://pyyaml.org/wiki/PyYAML) and not through requirements.txt. 

Windows 10:
    Go to [this](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml) page and download: PyYAML-3.11-cp27-cp27m-win32.whl   
    (If running 64-bit python or if you get a 'not a supported wheel on this platform' error, 
    download the 64 bit version instead: PyYAML-3.11-cp27-cp27m-win_amd64.whl )
```
$ cd download-directory
$ pip install PyYAML-3.11-cp27-cp27m-win32.whl
// (replace PyYAML-3.11-cp27-cp27m-win32.whl with PyYAML-3.11-cp27-cp27m-win_amd64.whl 
// if you needed to download the 64-bit version)
```
### Develop PokemonGo-Bot

```
$ git clone -b dev https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
$ virtualenv .  
$ source bin/activate  
$ pip install -r requirements.txt  
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

## Usage
    usage: pokecli.py [-h] -a AUTH_SERVICE -u USERNAME -p PASSWORD -l LOCATION [-lc] [-c] [-m] [-w] [--distance_unit] [--initial-transfer] [--maxsteps] [-iv] [-d] [-t] 

    optional arguments:
      -h, --help                                    show this help message and exit
      -a AUTH_SERVICE, --auth_service AUTH_SERVICE  Auth Service ('ptc' or 'google')
      -u USERNAME, --username USERNAME              Username
      -p PASSWORD, --password PASSWORD              Password
      -l LOCATION, --location LOCATION              Location (Address or 'xx.yyyy,zz.ttttt')
      -lc, --location_cache                         Bot will start at last known location
      -c CP, --cp                                   Set the CP to transfer or lower (eg. 100 will transfer CP0-99)
      -m MODE, --mode MODE                          Set farming Mode for the bot ('all', 'poke', 'farm')
      -w SPEED,  --walk SPEED                       Walk instead of teleport with given speed (meters per second max 4.16 because of walking end on 15km/h)
      -du, --distance_unit UNIT                     Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)
      -it, --initial_transfer                       Start the bot with a pokemon clean up, keeping only the higher CP of each pokemon. It respects -c as upper limit to release.
      -ms, --max_steps MAX_STEP                     Set the steps around your initial location (DEFAULT 5 mean 25 cells around your location)
      -iv IV, --pokemon_potential                   Set the ratio for the IV values to transfer (DEFAULT 0.4 eg. 0.4 will transfer a pokemon with IV 0.3)
      -d, --debug                                   Debug Mode
      -t, --test                                    Only parse the specified location


### Command Line Example
    Pokemon Trainer Club (PTC) account:
    $ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"
    Google Account:
    $ python2 pokecli.py -a google -u tejado -p 1234 --location "New York, Washington Square"


### Advance Releasing Configuration
    Sometimes filter desired pokemon with ``-iv`` is not enough. Some Pokemons have decent stats but their potential value is low because how the value distribted between stamina, attack, and defense. E.g. Charmeleon with IVs 15/15/0, its potential value is 0.67 which quite low - the truth is this dude is badass, you don't really need to care much about defense for this guy. He is fragile anyway xD
    
    To config the whitelist, copy file ``pkmn_whitelist.json.example`` and rename it to  ``pkmn_whitelist.json``
    Edit this file however you like, but keep in mind:
    1. Pokemon name is always capitalize and case-sensitive
    2. These settings will override ``-c`` and ``-iv``. Especially field ``any``, so use with caution.
    
=======

## How to run with Docker
    docker run namlehong/alpine-pgo:dev -a ptc -u tejado -p 1234 -l "New York, Central Park" -iv 0.8 -w 25


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

## FAQ

### What's IV ?
Here's the [introduction](http://bulbapedia.bulbagarden.net/wiki/Individual_values) 
### Losing Starter Pokemon and others
You can use -c 1 to protect your first stage low CP pokemon. 
### Does it run automatally?
Not yet, still need a trainer to train the script param. But we are very close to. 
### Set GEO Location
It works, use -l "xx.yyyy,zz.ttttt" to set lat long for location. -- diordache
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
Its a yaml file with a list of names so make it look like
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

## Contributors (Don't forget add yours here when you create PR:)
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
 * namlehong
 * gnekic(GeXx)
 * luizperes
 * brantje
 * VirtualSatai
 * dmateusp
 * jtdroste

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
