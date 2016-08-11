# PokemonGo-Bot
PokemonGo bot is a project created by the [PokemonGoF](https://github.com/PokemonGoF) team.

The project is currently setup in two main branches. `dev` also known as `beta` and `master` also known as `stable`. Submit your PR's to `dev`.

If you need any help please don't create an issue here on github we have a great community on Slack, [Click here to join the chat!](https://pokemongo-bot.herokuapp.com). You can count on the community in #help channel.

## Table of Contents
- [Installation](https://github.com/PokemonGoF/PokemonGo-Bot/blob/dev/docs/installation.md)
- [Documentation](https://github.com/PokemonGoF/PokemonGo-Bot/blob/dev/docs/)
- [Features](#features)
- [Credits](#credits)

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
- [x] Hatch eggs
- [x] Incubate eggs
- [ ] [Standalone Desktop Application] (https://github.com/PokemonGoF/PokemonGo-Bot-Desktop)
- [ ] Use candy
- [ ] Inventory cleaner

## Gym Battles
This bot takes a strong stance against automating gym battles. Botting gyms will have a negative effect on most players and thus the game as a whole. We will thus never accept contributions or changes containing code specific for gym battles.

## Analytics
This bot is very popular and has a vibrant community. Because of that, it has become very difficult for us to know how the bot is used and what errors people hit. By capturing small amounts of data, we can prioritize our work better such as fixing errors that happen to a large percentage of our user base, not just a vocal minority.

Our goal is to help inform our decisions by capturing data that helps us get aggregate usage and error reports, not personal information. To view the code that handles analytics in our master branch, you can use this [search link](https://github.com/PokemonGoF/PokemonGo-Bot/search?utf8=%E2%9C%93&q=BotEvent).

If there are any concerns with this policy or you believe we are tracking something we shouldn't, please open a ticket in the tracker. The contributors always intend to do the right thing for our users, and we want to make sure we are held to that path.

If you do not want any data to be gathered, you can turn off this feature by setting `health_record` to `false` in your `config.json`.

## Help Needed on [Desktop Version](https://github.com/PokemonGoF/PokemonGo-Bot-Desktop)


## Credits
- [tejado](https://github.com/tejado) many thanks for the API
- [U6 Group](http://pgoapi.com) for the U6
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff


[![Analytics](https://ga-beacon.appspot.com/UA-81468120-1/welcome-page-master)](https://github.com/igrigorik/ga-beacon)
