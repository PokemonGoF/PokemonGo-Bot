### Requirements (click each one for install guide)

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Recommended)
- [docker](https://docs.docker.com/engine/installation/) (Optional) - [how to setup after installation](https://github.com/PokemonGoF/PokemonGo-Bot/wiki/How-to-run-with-Docker)
- [protobuf 3](https://github.com/google/protobuf) (OS Dependent, see below)

#Linux/Mac Automatic installation
### Easy installation
1. Clone the git: `git clone https://github.com/PokemonGoF/PokemonGo-Bot`
2. Go into the new directory: `cd PokemonGo-Bot`
3. Run `./setup.sh -i`  
    This will install the bot and all stuff that is needed to run it (follow the steps in this process)
4. Run `./run.sh`  
    After you are done following it this will start your bot.

### To update
1. Stop the bot if it's running. (use control + c twice to stop it)
2. Run `./setup.sh -r`  
    This will reset and makes sure you have no changes made to any code since it will overide it
3. Rerun the bot `./run.sh`

#Windows Automatic installation
###TBA
