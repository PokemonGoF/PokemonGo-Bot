# Manual installation

## Table of Contents
- [Linux and Mac Installation](#linux-and-mac)
- [Windows](#windows)

### Linux and Mac
Ubuntu will be used for the Linux Example

####First install required packages

#####Linux
```bash
sudo apt-get install build-essential autoconf libtool pkg-config make python2.7-dev wget git
```
####
if you are on a different Linux OS you maybe have to adapt things like:

- package manager (for example yum instead of apt-get)
- package names

#####Mac
```bash
brew install --devel protobuf
brew install  autoconf libtool pkg-config wget git
```
####Mac + Linux installation
make sure you installed everything above

- get pip for python2.7
```bash
wget https://bootstrap.pypa.io/get-pip.py
python2.7 get-pip.py
rm -f get-pip.py
```

- switch to the location where you want to install it
- get git Repository and switch into the downloaded Folder

(Please keep in mind that master is not always up-to-date whereas 'dev' is. In the installation note below change `master` to `dev` if you want to get and use the latest version.)
```bash
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot  
cd PokemonGo-Bot
```
####
- install virtualenv and activate it
```bash
pip install virtualenv
virtualenv .
source bin/activate
```
####
- install the requirements and get the needed encryption.so

(we move `encrypt.so` to the root folder of the Bot so no need to edit the config regarding that)
```bash
pip install -r requirements.txt
wget http://pgoapi.com/pgoencrypt.tar.gz
tar -xzvf pgoencrypt.tar.gz
cd pgoencrypt/src/
make
cd ../../
mv pgoencrypt/src/libencrypt.so encrypt.so
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

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/) *Be sure to tick "Add python.exe to Path" during install*
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Microsoft Visual C++ Compiler for Python 2.7](http://www.microsoft.com/en-us/download/details.aspx?id=44266)


*Run the following commands in the Command Prompt with Administrator Privileges*

```
cd C:\Python27\
pip2 install --upgrade pip
pip2 install --upgrade virtualenv
pip2 install --upgrade protobuf==3.0.0b4
git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
```

##### Get encrypt.so and encrypt.dll or encrypt_64.dll
Due to copyright on the encrypt.so, encrypt.dll and encrypt_64.dll we are not directly hosting it. Please find a copy elsewhere on the internet and compile it yourself. We accept no responsibility should you encounter any problems with files you download elsewhere.
Try asking around our Slack chat **(Just say the word "encrypt" and Slackbot will give you info)**!

Download it to the `C:/Python27/PokemonGo-Bot/` folder

##### Update

*Run the following commands in the Command Prompt with Administrator Privileges*

```
cd C:/Python27/PokemonGo-Bot/
git pull
git submodule update --init --recursive
```
