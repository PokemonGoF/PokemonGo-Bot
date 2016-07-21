# PokemonGo-Bot - a pokemon script can catch pokemon and spin the pokestop.

## Features:
 * Search Fort(Spin Pokestop)
 * Catch Pokemon
 * Release low cp pokemon
 
## Usage

### PokemonGo-Bot
    usage: pokecli.py [-h] -a AUTH_SERVICE -u USERNAME -p PASSWORD -l LOCATION [-d] [-t]

    optional arguments:
      -h, --help                                    show this help message and exit
      -a AUTH_SERVICE, --auth_service AUTH_SERVICE  Auth Service ('ptc' or 'google')
      -u USERNAME, --username USERNAME              Username
      -p PASSWORD, --password PASSWORD              Password
      -l LOCATION, --location LOCATION              Location
      -d, --debug                                   Debug Mode
      -t, --test                                    Only parse the specified location


### PokemonGo-Bot

    $ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"
    2016-07-19 01:22:14,806 [   pokecli] [ INFO] Your given location: Washington Square, Greenwich, NY 12834, USA
    2016-07-19 01:22:14,806 [   pokecli] [ INFO] lat/long/alt: 43.0909305 -73.4989367 0.0
    2016-07-19 01:22:14,808 [  auth_ptc] [ INFO] Login for: tejado
    2016-07-19 01:22:15,584 [  auth_ptc] [ INFO] PTC Login successful
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Starting RPC login sequence (app simulation)
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Create new request...
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Adding 'GET_PLAYER' to RPC request
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Adding 'GET_HATCHED_EGGS' to RPC request
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Adding 'GET_INVENTORY' to RPC request
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Adding 'CHECK_AWARDED_BADGES' to RPC request
    2016-07-19 01:22:15,584 [    pgoapi] [ INFO] Adding 'DOWNLOAD_SETTINGS' to RPC request including arguments
    2016-07-19 01:22:15,585 [    pgoapi] [ INFO] Execution of RPC
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Cleanup of request!
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Finished RPC login sequence (app simulation)
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Login process completed
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Create new request...
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Adding 'GET_PLAYER' to RPC request
    2016-07-19 01:22:16,259 [    pgoapi] [ INFO] Execution of RPC
    2016-07-19 01:22:16,907 [    pgoapi] [ INFO] Cleanup of request!
    Response dictionary:
    ...
          "profile": {
            "username": "tejado",
            "item_storage": 350,
            "unknown12": "",
            "unknown13": "",
            "creation_time": 1468139...,
            "currency": [
              {
                "type": "POKECOIN"
              },
              {
                "amount": 400,
                "type": "STARDUST"
              }
            ],
            "daily_bonus": {},
            "avatar": {
              "unknown2": 1,
              "unknown3": 4,
              "unknown9": 2,
              "unknown10": 1
            },
            "tutorial": "AAEDBAc=\n",
            "poke_storage": 250
          },
    ...
    
## Requirements
 * Python 2
 * requests
 * protobuf
 * gpsoauth
 * geopy
 * s2sphere
 * googlemaps
 
    
## Credits
# The works are based on the Pokemon Go API
[tejado](https://github.com/tejado) for the API -- many thanks
[Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets  
[elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR  
[AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos  
[AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff

