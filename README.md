# PokemonGo-Bot - a pokemon script can catch pokemon and spin the pokestop.

## Features:
 * Search Fort(Spin Pokestop)
 * Catch Pokemon
 * Release low cp pokemon
 * Walking as you 

# To-Do:
- [ ] Limit the step to farm specific area for pokestops
- [ ] Drop items when bag is full
- [ ] Pokemon catch filter
- [ ] Hatch eggs
- [ ] Incubate eggs
- [ ] Evolve pokemons
- [ ] Use candy

## Installation

### Python Installation
    1. [Install Python 2.7](https://wiki.python.org/moin/BeginnersGuide/Download)
    1. [Install PIP](https://pip.pypa.io/en/stable/installing/)
### Google Protobuf Installation
    MAC:  brew update && brew install --devel protobuf 
### Install Pokemon_Go_Bot 

    1. Download or clone the repository.
    1. Using a terminal navigate into the clone repository.
    1. Install all requirements for the project using `pip install -r ./requirements.txt`
 
## Usage
    usage: pokecli.py [-h] -a AUTH_SERVICE -u USERNAME -p PASSWORD -l LOCATION [-w]  [-d] [-t] [-s] [-c]

    optional arguments:
      -h, --help                                    show this help message and exit
      -a AUTH_SERVICE, --auth_service AUTH_SERVICE  Auth Service ('ptc' or 'google')
      -u USERNAME, --username USERNAME              Username
      -p PASSWORD, --password PASSWORD              Password
      -l LOCATION, --location LOCATION              Location (Address or 'xx.yyyy,zz.ttttt')
      -w SPEED,  --walk SPEED                       Walk instead of teleport with given speed (meters per second max 4.16 becourse of walking end on 15km/h)
      -s SPINSTOP, --spinstop                       Enable Spinning of PokeStops
      -c CP, --cp                                   Set the CP to transfer or lower (eg. 100 will transfer CP0-99)
      -d, --debug                                   Debug Mode
      -t, --test                                    Only parse the specified location


### Command Line Example
    Pokomon Training Account:
    $ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"
    Google Account:
    $ python2 pokecli.py -a google -u tejado -p 1234 --location "New York, Washington Square"

## FAQ

### Set GEO Location
    It works, use -l "xx.yyyy,zz.ttttt" to set lat long for location. -- diordache
### FLEE
   The status code "3" corresponds to "Flee" - meaning your Pokemon has run away. 
   {"responses": { "CATCH_POKEMON": { "status": 3 } }
### My pokemon are not showing up in my Pokedex?
   Finish the tutorial on a smartphone. This will then allow everything to be visible.
### How can I maximise my XP per hour?
Quick Tip: When using this script, use a Lucky egg to double the XP for 30 mins. You will level up much faster. A Lucky egg is obtained on level 9 and further on whilst leveling up. (from VipsForever via /r/pokemongodev)



## Requirements
 * Python 2
 * requests
 * protobuf
 * gpsoauth
 * geopy
 * s2sphere
 * googlemaps


## Contributors
eggins -- The first pull request :)  
crack00r
ethervoid

## Credits
### The works are based on the Pokemon Go API
[tejado](https://github.com/tejado) many thanks for the API  
[Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets  
[elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR  
[AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos  
[AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff


## Donation

Bitcoin Address:  1PJMCx9NNQRasQYaa4MMff9yyNFffhHgLu

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=WQUXDC54W6EVY)
