# Disclaimer
©2016 Niantic, Inc. ©2016 Pokémon. ©1995–2016 Nintendo / Creatures Inc. / GAME FREAK inc. © 2016 Pokémon/Nintendo Pokémon and Pokémon character names are trademarks of Nintendo. The Google Maps Pin is a trademark of Google Inc. and the trade dress in the product design is a trademark of Google Inc. under license to The Pokémon Company. Other trademarks are the property of their respective owners.
[Privacy Policy](http://www.pokemon.com/us/privacy-policy/)

[PokemonGo-Bot](https://github.com/PokemonGoF/PokemonGo-Bot) is intended for academic purposes and should not be used to play the game *PokemonGo* as it violates the TOS and is unfair to the community. Use the bot **at your own risk**.

[PokemonGoF](https://github.com/PokemonGoF) does not support the use of 3rd party apps or apps that violate the TOS.

# PokemonGo-Bot
PokemonGo bot is a project created by the [PokemonGoF](https://github.com/PokemonGoF) team.

The project is currently setup in two main branches. 
- `dev` also known as `beta` - This is where the latest features are, but you may also experience some issues with stability/crashes
- `master` also known as `stable` - The bot 'should' be stable on this branch, and is generally well tested

## Support
###Configuration issues/help
If you need any help please don't create an issue as we have a great community on Slack. You can count on the community in [#help](https://pokemongo-bot.slack.com/messages/help/) channel.
 - [Click here to signup (first time only)](https://pokemongo-bot.herokuapp.com) 
 - [Join if you're already a member](https://pokemongo-bot.slack.com/messages/general/). 

###[Bugs / Issues](https://github.com/PokemonGoF/PokemonGo-Bot/issues?q=is%3Aissue+sort%3Aupdated-desc)
If you discover a bug in the bot, please [search our issue tracker](https://github.com/PokemonGoF/PokemonGo-Bot/issues?q=is%3Aissue+sort%3Aupdated-desc) first. If it hasn't been reported, please [create a new issue](https://github.com/PokemonGoF/PokemonGo-Bot/issues/new) and ensure you follow the template guide so that our team can assist you as quickly as possible.

###[Feature Requests](https://github.com/PokemonGoF/PokemonGo-Bot/labels/Feature%20Request)
If you have a great idea to improve the bot, please [search our feature tracker](https://github.com/PokemonGoF/PokemonGo-Bot/labels/Feature%20Request) first to ensure someone else hasn't already come up with the same great idea.  If it hasn't been requested, please [create a new request](https://github.com/PokemonGoF/PokemonGo-Bot/issues/new) and ensure you follow the template guide so that it doesnt get lost with the bug reports. 
While you're there vote on other feature requests to let the devs know what is most important to you.

###[Pull Requests](https://github.com/PokemonGoF/PokemonGo-Bot/pulls)
If you'd like to make your own changes, make sure you follow the pull request template, and ensure your PR is made against the 'dev' branch

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
- [x] Crowd Sourced Map Prototype
- [ ] [Standalone Desktop Application] (https://github.com/PokemonGoF/PokemonGo-Bot-Desktop)
- [ ] Use candy

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
- [Breeze ro](https://github.com/BreezeRo) for some of the MQTT/Map stuff

## [Contributors](https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/CONTRIBUTORS.md)


[![Analytics](https://ga-beacon.appspot.com/UA-81468120-1/welcome-page-master)](https://github.com/igrigorik/ga-beacon)
