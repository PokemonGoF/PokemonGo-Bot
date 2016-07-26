# PokemonGo-Bot
PokemonGo bot is a project created by the [PokemonGoF](https://github.com/PokemonGoF) team.
The project is currently setup in two different branches. `dev` and `master`.

We use [Slack](https://slack.com) as a web chat. [Click here to join the chat!](https://pokemongo-bot.herokuapp.com)

## Features
- [x] GPS Location configuration
- [x] Search Pokestops
- [x] Catch Pokemon
- [x] Determine which pokeball to use (uses Razz Berry if the catch percentage is low!)
- [x] Exchange Pokemon as per configuration
- [x] Evolve Pokemon as per configuration
- [x] Auto switch mode (Inventory Checks - switches between catch/farming items)
- [x] Limit the step to farm specific area for pokestops
- [x] Rudimentary IV Functionality filter
- [x] Ignore certain pokemon filter
- [ ] Standalone Desktop Application
- [ ] Hatch eggs
- [ ] Incubate eggs
- [ ] Use candy
- [ ] Fight Gym

## Wiki
All information on [Getting Started](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Getting-Started) is available in the [Wiki](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/)!
To ensure that all updates are documented - [@eggins](https://github.com/eggins) will keep the Wiki updated with the latest information on installing, updating and configuring the bot.

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



## OLD README BELOW. STILL UPDATING THIS.

## Table of Contents
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

### Note on branch
Please keep in mind that master is not always up-to-date whereas 'dev' is. In the installation note below change `master` to `dev` if you want to get and use the latest version.

### Installation Linux
(change master to dev for the latest version)

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Installation Mac
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

### Installation Windows
(change master to dev for the latest version)

On Windows, you will need to install PyYaml through the installer and not through requirements.txt.

##### Windows vista, 7, 8:
Go to : http://pyyaml.org/wiki/PyYAML , download the right version for your pc and install it

##### Windows 10:
Go to [this](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml) page and download: PyYAML-3.11-cp27-cp27m-win32.whl   
(If running 64-bit python or if you get a 'not a supported wheel on this platform' error,
download the 64 bit version instead: PyYAML-3.11-cp27-cp27m-win_amd64.whl )

*(Run the following commands from Git Bash.)*

```
// switch to the directory where you downloaded PyYAML
$ cd download-directory
// install 32-bit version
$ pip2 install PyYAML-3.11-cp27-cp27m-win32.whl
// if you need to install the 64-bit version, do this instead:
// pip2 install PyYAML-3.11-cp27-cp27m-win_amd64.whl
```

After this, just do:

```
$ git clone -b master https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
$ pip2 install -r requirements.txt
$ git submodule init
$ git submodule update
```

### Develop PokemonGo-Bot

```
$ git clone -b dev https://github.com/PokemonGoF/PokemonGo-Bot  
$ cd PokemonGo-Bot  
// create virtualenv using Python 2.7 executable
$ virtualenv -p C:\python27\python.exe venv
$ source venv/Scripts/activate  
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
  1. copy `config.json.example` to `config.json` and `release_config.json.example` to `release_config.json`
  2. Edit `config.json` and replace `auth_service`, `username`, `password`, `location` and `gmapkey` with your parameters (other keys are optional, check `Advance Configuration` below)

## Advance Configuration
Option | Meaning
------ | -------
`max_steps` |		The steps around your initial location (DEFAULT 5 mean 25 cells around your location) that will be explored
`mode` |  		Set farming Mode for the bot ('all', 'poke', 'farm'). 'all' means both spinning pokéstops and catching pokémon; 'poke'means only catching pokémon and 'farm' means only spinning pokéstops
`walk` | Walk with the given speed (meters per second max 4.16 because of walking end on 15km/h)
`debug` | 		Let the default value here except if you are developer
`test` | 		Let the default value here except if you are developer
`initial_transfer` | 	Set this to an upper bound of the cp level which you want to transfer at the beginning of the run. For example, set the value to 0 to disable the initial transfer, set it to 100 to enable initial transfer for cp levels 0-99. It will still transfer pokémon during your exploration, depending on how your release_config.json is setup.
`location_cache` | Bot will start at last known location if you do not have location set in the config
`distance_unit` | 	Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)
`item_filter` | 	Pass a list of unwanted items (in CSV format) to recycle when collected at a Pokestop (e.g, "101,102,103,104" to recycle potions when collected)
`evolve_all` | 	Set to true to evolve pokemons if possible, takes pokémon as an argument as well.

## Catch Configuration
Default configuration will capture all Pokemon.
```"any": {"catch_above_cp": 0, "catch_above_iv": 0, "logic": "or"}```
You can override the global configuration with Pokemon-specific options, such as:
```"Pidgey": {"catch_above_cp": 0, "catch_above_iv": 0.8", "logic": "and"}```
to only capture Pidgey with a good roll.
Additionally, you can specify always_capture and never_capture flags. For example:
```"Pidgey": {"never_capture": true}```
will stop catching Pidgey entirely.

## Release Configuration
Default configuration will not release any Pokemon.
```"any": {"release_below_cp": 0, "release_below_iv": 0, "logic": "or"}```
You can override the global configuration with Pokemon-specific options, such as:
```"Pidgey": {"release_below_cp": 0, "release_below_iv": 0.8", "logic": "or"}```
to only release Pidgey with bad rolls.
Additionally, you can specify always_release and never_release flags. For example:
```"Pidgey": {"always_release": true}```
will release all Pidgey caught.

### Evolve All Configuration
    By setting the `evolve_all` attribute in config.json, you can instruct the bot to automatically
    evolve specified pokemons on startup. This is especially useful for batch-evolving after popping up
    a lucky egg (currently this needs to be done manually).
    
    The evolve all mechanism evolves only higher IV/CP pokemons. It works by sorting the high CP pokemons (default: 300 CP or higher)
    based on their IV values. After evolving all high CP pokemons, the mechanism will move on to evolving lower CP pokemons
    only based on their CP (if it can).
    It will also automatically transfer the evolved pokemons based on the release configuration.
    
    Examples on how to use (set in config.json):
    
    1. "evolve_all": "all"
      Will evolve ALL pokemons.
    2. "evolve_all": "Pidgey,Weedle"
      Will only evolve Pidgey and Weedle.
    3. Not setting evolve_all or having any other string would not evolve any pokemons on startup.
    
    If you wish to change the default threshold of 300 CP, simply add the following to the config file:
    	"cp_min": <number>
    

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
On a local machine this would be http://127.0.0.1. On AWS this is your public DNS if you haven't configured an elastic IP.

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

### Does it run automatically?
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
