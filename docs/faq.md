### Do I need hashing key?
The bot will not run without a vaild hashing key. Learn more about - [hashing key here](http://hashing.pogodev.org).

### Does the bot support 2Captcha service?
Yes. Please include your 2Captcha token in auth.json
```
"2captcha_token": "YOUR_KEY_HERE"
```

### Does the bot support manual Captcha solving?
Yes. Please download chrome driver for your os plaform and place it into the root directory of the bot.
More information on [chrome driver here](https://sites.google.com/a/chromium.org/chromedriver/).

### How do I start the application?
After [installing] (https://github.com/PokemonGoF/PokemonGo-Bot/blob/dev/docs/installation.md), in the root folder run the following command:
### Linux
```
run.sh
```
### Windows
```
run.bat
```
This will start the application.

### Python possible bug
If you encounter problems with the module `ssl` and it's function `_create_unverified_context`, just comment it. (Solution available in Python 2.7.11)
In order to comment out the function and the module, please follow the instructions below:
- edit `pokecli.py`
- put `#` before `if` (line 43) and `ssl` (line 44)
- save it

Please keep in mind that this fix is only necessary if your python version don't have the `_create_unverified_context` argument in the ssl module.

### What's IV?
Here's the [introduction](http://bulbapedia.bulbagarden.net/wiki/Individual_values)

### Does it run automatically?
Not yet, still need a trainer to train the script param. But we are very close to.

### Set GEO Location
It works, use "location": "59.333409,18.045008", in configs/config.json to set lat long for location. Use a Pokemon Go map to find an area with pokemons you still need (e.g. [https://pokevision.com/](https://pokevision.com/)), however don't jump too big distances (see "softban").

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

### How do I use the map??
[See wiki info here] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Google-Maps-API-(web-page))

### No JSON object could be decoded or decoder.py error
If you see "No JSON object could be decoded" or you see "decoder.py" in the last part of the error, this means that there is something wrong with your JSON.

Copy the json in json files and copy it into http://jsonlint.com/  Then fix the error it gives you in your json.
