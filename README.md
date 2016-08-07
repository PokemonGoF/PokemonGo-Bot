
# PokemonGo-Bot (Working)
PokemonGo bot is a project created by the [PokemonGoF](https://github.com/PokemonGoF) team.
The project is currently setup in two main branches. `dev` and `master`.

## Please submit PR to [Dev branch](https://github.com/PokemonGoF/PokemonGo-Bot/tree/dev)

## Where to get the DLL/SO? A help channel is coming.
You need to grab them from the Internet.

We use [Slack](https://slack.com) as a web chat. [Click here to join the chat!](https://pokemongo-bot.herokuapp.com)

## Table of Contents
- [Features](#features)
- [Wiki](#wiki)
- [Credits](#credits)
- [Donation](#donation)


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
- [x] Adjust delay between Pokemon capture & Transfer as per configuration
- [ ] Standalone Desktop Application
- [x] Hatch eggs
- [x] Incubate eggs
- [ ] Use candy
- [ ] Inventory cleaner

## Gym Battles
This bot takes a strong stance against automating gym battles. Botting gyms will have a negative effect on most players and thus the game as a whole. We will thus never accept contributions or changes containing code specific for gym battles.

## Analytics
This bot is very popular and has a vibrant community. Because of that, it has become very difficult for us to know how the bot is used and what errors people hit. By capturing small amounts of data, we can prioritize our work better such as fixing errors that happen to a large percentage of our user base, not just a vocal minority.

Our goal is to help inform our decisions by capturing data that helps us get aggregate usage and error reports, not personal information. To view the code that handles analytics in our master branch, you can use this [search link](https://github.com/PokemonGoF/PokemonGo-Bot/search?utf8=%E2%9C%93&q=BotEvent).

If there are any concerns with this policy or you believe we are tracking something we shouldn't, please open a ticket in the tracker. The contributors always intend to do the right thing for our users, and we want to make sure we are held to that path.

If you do not want any data to be gathered, you can turn off this feature by setting `health_record` to `false` in your `config.json`.

## Wiki
All information on [Getting Started](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Getting-Started) is available in the [Wiki](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/)!
- __Installation__
  - [Requirements] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation#requirements-click-each-one-for-install-guide)
  - [How to run with Docker](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/How-to-run-with-Docker)
  - [Linux] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation#installation-linux)
  - [Mac] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation#installation-mac)
  - [Windows] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Installation#installation-windows)
- [Develop PokemonGo-Bot](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Develop-PokemonGo-Bot)
- [Configuration-files](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Configuration-files)
- [Front end web module - Google Maps API] (https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Google-Maps-API-(web-page))
- [Docker Usage](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/FAQ#how-to-run-with-docker)
- [FAQ](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/FAQ)

To ensure that all updates are documented - [@eggins](https://github.com/eggins) will keep the Wiki updated with the latest information on installing, updating and configuring the bot.

## Credits
- [tejado](https://github.com/tejado) many thanks for the API
- [U6 Group](http://pgoapi.com) for the U6
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff


[![Analytics](https://ga-beacon.appspot.com/UA-81468120-1/welcome-page-master)](https://github.com/igrigorik/ga-beacon)
