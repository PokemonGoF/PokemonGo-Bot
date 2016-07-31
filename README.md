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
## Help with the project [Dev Bot](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Develop-PokemonGo-Bot)
## Project Chat
We use [Slack](https://slack.com) as a web chat. [Click here to join the chat!](https://pokemongo-bot.herokuapp.com)
## Breaking Changes
You need modify config.json (config.json.pokemon.example for example) then python pokecli.py --config configs/config.json

[More details about config file](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Configuration-files)
Please clean up your old clone if you have issue, and following the [install instruction](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation).

## About dev/master Branch
Dev branch has the most up-to-date features, but be aware that there might be some broken changes. Your contribution and PR for fixes are warm welcome.
Master branch is the stable branch.
No PR on master branch to keep things easier.
## Table of Contents
- [Project Chat](#project-chat)
- [Features](#features)
- [TODO List](#todo-list)
- [Usage](#usage)
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
 * Drop items
 * Pokemon catch filter 
 * Google Map API key setup
 * Show all objects on map (In Testing)
 * Evolve pokemons (Code in, Need input, In Testing)
 * Incubate eggs
 * Hatch eggs
 * Pokemon transfer filter

## TODO List

- [ ] Standalone Desktop APP
- [ ] Use candy
- [ ] Softban Bypass (In Development)

## Gym Battles
This bot takes a strong stance against automating gym battles. Botting gyms will have a negative effect on most players and thus the game as a whole. We will thus never accept contributions or changes containing code specific for gym battles.

## Installation
[Getting started guide](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Getting-Started)
[Jump right into installing](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation)

### Note on virtualenv
We recommend you use virtualenv, not only will this tool keep your OS clean from all the python plugins.
It also provide an virtual space for more than 1 instance!

### Protobuf 3 installation Notes

- OS X:  `brew update && brew install --devel protobuf`
- Windows: Download protobuf 3.0: [here](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip) and unzip `bin/protoc.exe` into a folder in your PATH.
- Linux: `sudo apt-get install python-protobuf`

### Note on branch
Please keep in mind that master is not always up-to-date whereas 'dev' is. In the installation note below change `master` to `dev` if you want to get and use the latest version.

Make sure you install the following first:
[Requirements](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation)

### Google Maps API Bot Tracker
[Wiki on using the bot web folder](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Google-Maps-API-(web-page)

### FAQ
[Tips & Tricks](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/FAQ)

## How to run with Docker
[Wiki on how to use Docker](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/How-to-run-with-Docker)

## How to add/discover new API
The example is [here](https://github.com/PokemonGoF/PokemonGo-Bot/commit/46e2352ce9f349cc127a408959679282f9999585)

1. Check the type of your API request in   [POGOProtos](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/RequestType.proto) For example: RECYCLE_INVENTORY_ITEM

2. Convert to the api call in pokemongo_bot/__init__.py,  RECYCLE_INVENTORY_ITEM change to self.api.recycle_inventory_item

  ```python
  def drop_item(self,item_id,count):
    self.api.recycle_inventory_item(...............)
  ```
  
3. Where is the param list?
   You need check this [Requests/Messages/RecycleInventoryItemMessage.proto](https://github.com/AeonLucid/POGOProtos/blob/eeccbb121b126aa51fc4eebae8d2f23d013e1cb8/src/POGOProtos/Networking/Requests/Messages/RecycleInventoryItemMessage.proto)

4. Then our final api call is

  ```python
    def drop_item(self,item_id,count):
      self.api.recycle_inventory_item(item_id=item_id,count=count)
      inventory_req = self.api.call()
      print(inventory_req)
  ```
5. You can now debug on the log to see if get what you need

## FAQ
[Wiki Link](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/FAQ)

### What's IV ?
Here's the [introduction](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Pokemon-IV)
Research Website [Nice Tool](https://thesilphroad.com/research)

### What are the Item ID
[Wiki](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Item-ID's)

##Softban
[Wiki](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Softban)

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
 * GregTampa

-------
## Credits
- [tejado](https://github.com/tejado) many thanks for the API
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff


[![Analytics](https://ga-beacon.appspot.com/UA-81468120-1/welcome-page-master)](https://github.com/igrigorik/ga-beacon)
