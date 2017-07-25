# Manual installation

The bot now requires a hashing key from pogodev/Bossland [hashing key](http://hashing.pogodev.org)

## Table of Contents

- [Linux and Mac Installation](#linux-and-mac)
- [Windows](#windows)

### Linux and Mac

Ubuntu will be used for the Linux Example

#### First install required packages

##### Linux - Ubuntu

```bash
sudo apt-get install build-essential autoconf libtool pkg-config make python2.7-dev wget git
```

##### Linux - Centos 7

```bash
sudo yum install -y epel-release
sudo yum install -y git wget python python-pip
sudo yum groupinstall -y "Development Tools"
```

####

if you are on a different Linux OS you maybe have to adapt things like:

- package manager (for example yum instead of apt-get)
- package names

##### Mac

```bash
brew install autoconf libtool pkg-config wget git
```

#### Mac + Linux installation

Make sure you installed everything above before proceeding.

- get pip for python2.7
```bash
wget https://bootstrap.pypa.io/get-pip.py
python2.7 get-pip.py
rm -f get-pip.py
```
- switch to the location where you want to install it
- get git Repository and switch into the downloaded Folder

(Please keep in mind that `master` is stable and tested but `dev` is bleeding edge. In the installation note below change `master` to `dev` if you want to get and use the latest version.)
```bash
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot  
cd PokemonGo-Bot
```

####

- install `virtualenv` and activate it
```bash
pip install virtualenv
virtualenv .
source bin/activate
```

####

- install the requirements
```bash
pip install -r requirements.txt
make
cd ../../
```

####

- copy and edit the config
(after copying it you can use any editor you like if you don't like `vi`) 
```bash
cp configs/config.json.example configs/config.json
vi configs/config.json
cp configs/auth.json.example configs/auth.json
vi configs/auth.json
```

####

- make sure your git repo is up to date
(make sure you are in the bot folder and activated virtualenv)
```bash
git pull
pip install -r requirements.txt
```

####

- finally start the bot
```bash
./run.sh
```

####

- after reboot or closing the terminal at every new start go into the folder of the PokemonGo-Bot by going into the folder where you started installing it and then
```bash
cd PokemonGo-Bot
#activate virtualenv and start
source bin/activate
./run.sh
```


### Windows

##### Requirements

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/) 
- *Be sure to tick "Add python.exe to Path" during as seen here:* ![Add Python To Path](http://i.imgur.com/RhYnhg0.jpg)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Microsoft Visual C++ Compiler for Python 2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266)


*Run the following commands in the Command Prompt with Administrator Privileges*

```
cd C:\Python27\
pip install --upgrade pip
pip install --upgrade virtualenv
git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot
pip install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
```

##### Update

*Run the following commands in the Command Prompt with Administrator Privileges*

```
cd C:/Python27/PokemonGo-Bot/
git pull
pip uninstall pgoapi
git submodule update --init --recursive
```
