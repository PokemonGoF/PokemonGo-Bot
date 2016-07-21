# PokemonGo-Bot - a pokemon script can catch pokemon and spin the pokestop.

## Features:
 * Search Fort(Spin Pokestop)
 * Catch Pokemon
 * Release low cp pokemon
 * Walking as you

## Installation

### Python Installation
    Install Python 2.7
    Install pip
    `pip install -r requirements.txt`
### Google Protobuf Installation
    MAC:  brew update && brew install --devel protobuf
## Usage
    usage: pokecli.py [-h] -a AUTH_SERVICE -u USERNAME -p PASSWORD -l LOCATION [-w]  [-d] [-t] [-s] [-c]

    optional arguments:
      -h, --help                                    show this help message and exit
      -a AUTH_SERVICE, --auth_service AUTH_SERVICE  Auth Service ('ptc' or 'google')
      -u USERNAME, --username USERNAME              Username
      -p PASSWORD, --password PASSWORD              Password
      -l LOCATION, --location LOCATION              Location
      -w SPEED,  --walk SPEED                       Walk instead of teleport with given speed (meters per second. max. 4.16 becourse of max 15km/h for walking)
      -s SPINSTOP, --spinstop                       Enable Spinning of PokeStops
      -c CP, --cp                                   Set the CP to transfer or lower (eg. 100 will transfer CP0-99)
      -d, --debug                                   Debug Mode
      -t, --test                                    Only parse the specified location


### Command Line Example

    $ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"

## FAQ

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
