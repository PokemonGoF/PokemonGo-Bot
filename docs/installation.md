#Install the bot
## Table of Contents
- [Linux or Mac Automatic Installation](#Linux/Mac)
- [Windows Automatic Installation](#windows)
- [Docker Automatic Installation](#docker)


#Linux/Mac

### Requirements (click each one for install guide)
- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)

### Easy installation
1. Clone the git: `git clone https://github.com/PokemonGoF/PokemonGo-Bot`
2. Go into the new directory: `cd PokemonGo-Bot`
3. Run `./setup.sh -i`  
    This will install the bot and all stuff that is needed to run it (follow the steps in this process)
4. Run `./run.sh`  
    After you are done following it this will start your bot.

### To update the bot
1. Stop the bot if it's running. (use control + c twice to stop it)
2. Run `./setup.sh -r`  
    This will reset and makes sure you have no changes made to any code since it will overide it
3. Rerun the bot `./run.sh`

for manual installation please refer to [here](https://github.com/nivong/PokemonGo-Bot/blob/dev/docs/manual_installation.md)

#Windows
##Requirements

[Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)

[git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

[Protoc](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip)

[Microsoft Visual C++ Compiler for Python 2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266)

###Easy Installation
1. Go into the folder/dir named: Windows bot
2. Run `PokemonGo-Bot-install.bat`
After that has done the bot will be installed
3. Run `PokemonGo-Bot-StartBot.bat`
This will start the bot itself
OPTIONAL: 4. Run `PokemonGo-Bot-StartServer.bat`
This will start the web interface and is optional stap

### To update the bot
1. Stop the bot by closing everything
2. Run `PokemonGo-Bot-Update.bat`
3. Rerun the bot by using `PokemonGo-Bot-StartBot.bat`

### To repair the bot if it isn't working for some reason
1. Stop the bot by closing everything
2. Run `PokemonGo-Bot-Repair.bat`
3. Rerun the bot by using `PokemonGo-Bot-StartBot.bat`

#Docker
##Requirements
- [docker](https://docs.docker.com/engine/installation/) (Optional) - [how to setup after installation](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/How-to-run-with-Docker)