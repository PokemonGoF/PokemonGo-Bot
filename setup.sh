#!/usr/bin/env bash
#encoding=utf8
pokebotpath=$(cd "$(dirname "$0")"; pwd)
webpath=$pokebotpath"/web"
backuppath=$pokebotpath"/backup"

function Pokebotupdate () {
cd $pokebotpath
git pull
git submodule update --init --recursive
git submodule foreach git pull origin master
source bin/activate
pip install -r requirements.txt --upgrade
pip install -r requirements.txt
}

function Pokebotescapestring () {
echo "$1" | sed 's/\//\\\//g' | sed 's/"/\\"/g' # escape slash and double quotes
}

function Pokebotauth () {
cd $pokebotpath
read -p "
-----------------
Auth generator
Enter 1 for Google or 2 for Pokemon Trainer Club (PTC)
-----------------
" auth
read -p "Input E-Mail (Google) or Username (PTC)
" username
read -p "Input Password
" -s password
password=$(Pokebotescapestring $password)
read -p "
Input Location
" location
read -p "Input Google API Key (gmapkey)
" gmapkey
read -p "Input Hashing servers key  (hashkey)
" hashkey
[[ $auth = "2" || $auth = "ptc" ]] && auth="ptc" || auth="google"
sed -e "s/YOUR_USERNAME/$username/g" -e "s/YOUR_PASSWORD/$password/g" \
  -e "s/SOME_LOCATION/$location/g" -e "s/GOOGLE_MAPS_API_KEY/$gmapkey/g" \
  -e "s/YOUR_PURCHASED_HASH_KEY/$hashkey/g"  \
  -e "s/google/$auth/g" configs/auth.json.example > configs/auth.json
echo "Edit ./configs/auth.json to modify auth or location."
}

function Pokebotconfig () {
cd $pokebotpath
read -p "
-----------------
Config Generator
Enter 1 for default, 2 for cluster, 3 for map, 4 for optimizer, 5 for path or 6 pokemon config
-----------------

" cfgoption
[ "$cfgoption" == "1" ] && cfgoption="config.json.example"
[ "$cfgoption" == "2" ] && cfgoption="config.json.cluster.example"
[ "$cfgoption" == "3" ] && cfgoption="config.json.map.example"
[ "$cfgoption" == "4" ] && cfgoption="config.json.optimizer.example"
[ "$cfgoption" == "5" ] && cfgoption="config.json.path.example"
[ "$cfgoption" == "6" ] && cfgoption="config.json.pokemon.example"
cp configs/$cfgoption configs/config.json
echo "Edit ./configs/config.json to modify any other config."
}

function Webconfig () {
cd $webpath
if [ -f config/userdata.js.example ]; then
echo "
-----------------
Configure userdata.js for web
-----------------
"
read -p "Input E-Mail (Google) or Username (PTC)
" webusername
read -p "Input Google API Key (gmapkey)
" webgmapkey
sed -e "s/username1/$webusername/g" -e "s/YOUR_API_KEY_HERE/$webgmapkey/g" \
  config/userdata.js.example > config/userdata.js
echo "Your userdata.js is now configured."
else 
echo "You do not yet have the web files installed. Please first run 'setup.sh -i' to install all the files."
fi
}

function Pokebotinstall () {
cd $pokebotpath
if [ "$(uname -s)" == "Darwin" ]
then
echo "You are on macOS"
elif [ $(uname -s) == CYGWIN* ]
then
echo "You are on Cygwin"
if [ !-x "$(command -v apt-cyg)" ]
then
wget http://apt-cyg.googlecode.com/svn/trunk/apt-cyg
chmod +x apt-cyg
mv apt-cyg /usr/local/bin/
fi
apt-cyg install gcc-core make
easy_install pip
elif [ -x "$(command -v apt-get)" ]
then
echo "You are on Debian/Ubuntu"
sudo apt-get update
sudo apt-get -y install python python-pip python-dev gcc make git
elif [ -e /etc/fedora-release ]
then
echo "You are on Fedora"
sudo dnf update
sudo dnf -y install redhat-rpm-config gcc make git
sudo dnf -y install python2 python-devel python-virtualenv
sudo pip install --upgrade pip
elif [ -x "$(command -v yum)" ]
then
echo "You are on CentOS/RedHat"
sudo yum -y install epel-release gcc make
sudo yum -y install python-pip python-devel
elif [ -x "$(command -v pacman)" ]
then
echo "You are on Arch Linux"
sudo pacman -Sy python2 python2-pip gcc make
elif [ -x "$(command -v dnf)" ]
then
echo "You are on Fedora/RHEL"
sudo dnf update
sudo dnf -y install python-pip python-devel gcc make
elif [ -x "$(command -v zypper)" ]
then
echo "You are on Open SUSE"
sudo zypper update
sudo zypper -y install python-pip python-devel gcc make
else
echo "Please check if you have python, pip, gcc and make installed on your device."
echo "Wait 5 seconds to continue or use ctrl+c to interrupt this shell."
sleep 5
fi
if [ ! -e /etc/fedora-release ]
then
easy_install virtualenv
fi
Pokebotreset
Pokebotupdate
echo "Install complete. Starting to generate auth.json and config.json and userdata.js for web."
Pokebotauth
Pokebotconfig
Webconfig
echo "You can now use the bot by executing 'run.sh'. You may also start the web tracker by executing 'web.sh'."
}

function Pokebotreset () {
cd $pokebotpath
git fetch -a
if [ "1" == $(git branch -vv |grep -c "* dev") ]
then
echo "Branch dev resetting."

git reset --hard origin/dev
elif [ "1" == $(git branch -vv |grep -c "* master") ]
then
echo "Branch master resetting."
git reset --hard origin/master
fi
if [ -x "$(command -v python2)" ]
then
virtualenv -p python2 .
else
virtualenv .
fi
Pokebotupdate
}

function Pokebothelp () {
echo "usage:"
echo "	-i,--install.		Install PokemonGo-Bot."
echo "	-b,--backup.		Backup config files."
echo "	-a,--auth.		Easy auth generator."
echo "	-c,--config.		Easy config generator."
echo "	-w,--web.		Web config generator."
echo "	-r,--reset.		Force sync source branch."
echo "	-u,--update.		Command git pull to update."
}

case $* in
--install|-i)
Pokebotinstall
;;
--reset|-r)
Pokebotreset
;;
--update|-u)
Pokebotupdate
;;
--backup|-b)
mkdir -p $backuppath
cp -f $pokebotpath/configs/auth*.json $backuppath/
cp -f $pokebotpath/configs/config*.json $backuppath/
cp -f $pokebotpath/configs/*.gpx $backuppath/
cp -f $pokebotpath/configs/path*.json $backuppath/
cp -f $pokebotpath/web/config/userdata.js $backuppath/
echo "Backup complete."
;;
--auth|-a)
Pokebotauth
;;
--config|-c)
Pokebotconfig
;;
--web|-w)
Webconfig
;;
--help|-h)
Pokebothelp
;;
*.json)
filename=$*
echo "It's better to use run.sh, not this one."
cd $pokebotpath
if [ ! -f ./configs/"$filename" ]
then
echo "There's no ./configs/"$filename" file. It's better to use run.sh, not this one."
else
./run.sh ./configs/"$filename"
fi
;;
*)
Pokebothelp
;;
esac
exit 0
