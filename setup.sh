#!/usr/bin/env bash
#encoding=utf8  
pokebotpath=$(cd "$(dirname "$0")"; pwd)
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

function Pokebotencrypt () {
echo "Start to make encrypt.so."
if [ -x "$(command -v curl)" ]
then
curl -O http://pgoapi.com/pgoencrypt.tar.gz
else
wget http://pgoapi.com/pgoencrypt.tar.gz
fi
tar -xf pgoencrypt.tar.gz 
cd pgoencrypt/src/ 
make
mv libencrypt.so $pokebotpath/encrypt.so
cd ../..
rm -rf pgoencrypt.tar.gz
rm -rf pgoencrypt
}

function Pokebotconfig () {
cd $pokebotpath
read -p "enter 1 for google or 2 for ptc 
" auth
read -p "Input username 
" username
read -p "Input password 
" -s password
read -p "
Input location 
" location
read -p "Input gmapkey 
" gmapkey
cp -f configs/config.json.example configs/config.json && chmod 755 configs/config.json
if [ "$auth" = "2" ] || [ "$auth" = "ptc" ]
then
sed -i "s/google/ptc/g" configs/config.json
fi
sed -i "s/YOUR_USERNAME/$username/g" configs/config.json
sed -i "s/YOUR_PASSWORD/$password/g" configs/config.json
sed -i "s/SOME_LOCATION/$location/g" configs/config.json
sed -i "s/GOOGLE_MAPS_API_KEY/$gmapkey/g" configs/config.json
echo "Edit ./configs/config.json to modify any other config."
}

function Pokebotinstall () {
cd $pokebotpath
if [ "$(uname -s)" == "Darwin" ]
then
echo "You are on Mac os"
sudo brew update 
sudo brew install --devel protobuf
elif [ -x "$(command -v apt-get)" ]
then
echo "You are on Debian/Ubuntu"
sudo apt-get update
sudo apt-get -y install python python-pip python-dev gcc make git
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
echo "Please check if you have  python pip gcc make  installed on your device."
echo "Wait 5 seconds to continue or Use ctrl+c to interrupt this shell."
sleep 5
fi
sudo pip install virtualenv
Pokebotreset
Pokebotupdate
Pokebotencrypt
echo "Install complete. Starting to generate config.json."
Pokebotconfig
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
echo "Branch master resetting"
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
echo "	-c,--config.		Easy config generator."
echo "	-e,--encrypt.		Make encrypt.so."
echo "	-r,--reset.		Force sync origin branch."
echo "	-u,--update.		Command git pull to update."
}

case $* in
--install|-i)
Pokebotinstall
;;
--encrypt|-e)
Pokebotencrypt
;;
--reset|-r)
Pokebotreset
;;
--update|-u)
Pokebotupdate
;;
--backup|-b)
mkdir -p $backuppath
cp -f $pokebotpath/configs/config*.json $backuppath/
cp -f $pokebotpath/configs/*.gpx $backuppath/
cp -f $pokebotpath/configs/path*.json $backuppath/
cp -f $pokebotpath/web/config/userdata.js $backuppath/
echo "Backup complete."
;;
--config|-c)
Pokebotconfig
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
