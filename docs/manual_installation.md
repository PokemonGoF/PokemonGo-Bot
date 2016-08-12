# Manual installation

## Table of Contents
- [Linux Installation](#linux)
- [Mac Installation](#mac)
- [Windows](#windows)

### Linux and Mac
Ubuntu will be used for the Linux Example

####First install requierd packages

#####Linux
```bash
sudo apt-get install build-essential autoconf libtool pkg-config make python-dev python-protobuf python2.7 wget git
```
#####Mac
```bash
brew install --devel protobuf
brew install  autoconf libtool pkg-config wget git
```
####Mac + Linux installation
make shure you installed everything above

- get pip for pyton2.7
```bash
wget https://bootstrap.pypa.io/get-pip.py
python2.7 get-pip.py
rm -f get-pip.py
```
- switch to the location where you want to install it
- get git Repository and switch into the downloaded Folder
```bash
git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot  
cd PokemonGo-Bot
```
- install virtualenv and activate it
```bash
pip install virtualenv
virtualenv .
```
- install the requirements and get the needen encryption.so
- 
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
- copy and edit the config
(after copying it you can use any editor you like if you don't like `vi`) 
```bash
cp configs/config.json.example configs/config.json
vi configs/config.json
```
- make shure your git repo is up to date
(make shure you are in the bot folder and activated virtualenv)
```bash
git pull
pip install -r requirements.txt
```
- finaly start the bot
```bash
./run.sh configs/config.json
```
after reboot or closing the terminal
at every new start go into the folder of the PokemonGo-Bot by
going into the folder where you startet installing it an then
```bash
cd PokemonGo-Bot
#activate virtualenv and start
source bin/activate
./run.sh configs/config.json
```
if you are on a different Linux OS you maybe have to adapt things like:

- package mananger (for example yum instead of apt-get)
- package names


### Windows
WIP

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
$ virtualenv .
$ script\activate
$ pip2 install -r requirements.txt
$ git submodule init
$ git submodule update
```



### Protobuf 3 installation

- OS X:  `brew update && brew install --devel protobuf`
- Windows: Download protobuf 3.0: [here](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip) and unzip `bin/protoc.exe` into a folder in your PATH.

### Get encrypt.so (Windows part writing need fine tune)
Due to copywrite on the encrypt.so we are not directly hosting it. Please find a copy elsewhere on the internet and compile it yourself. We accept no responsibility should you encounter any problems with files you download elsewhere.

Ensure you are in the PokemonGo-Bot main folder and run:

`wget http://pgoapi.com/pgoencrypt.tar.gz && tar -xf pgoencrypt.tar.gz && cd pgoencrypt/src/ && make && mv libencrypt.so ../../encrypt.so && cd ../..`

### Note on branch
Please keep in mind that master is not always up-to-date whereas 'dev' is. In the installation note below change `master` to `dev` if you want to get and use the latest version.

## Update
To update your project do (in the project folder): `git pull`

To update python requirement packages do (in the project folder): `pip install --upgrade -r requirements.txt`

