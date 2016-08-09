#!/bin/bash
pokebotpath=$(pwd)
backuppath=$(pwd)“/backup"

function Pokebotupdate () {
cd $pokebotpath
git pull
git submodule init
git submodule foreach git pull origin master
virtualenv .
source bin/activate
pip install -r requirements.txt
}

function Pokebotencrypt () {
echo "Start to make encrypt.so"
wget http://pgoapi.com/pgoencrypt.tar.gz
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
read -p "1.google 2.ptc 
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
cp configs/config.json.example configs/config.json
if [ "$auth" = "2" ]
then
sed -i "s/google/ptc/g" configs/config.json
fi
sed -i "s/YOUR_USERNAME/$username/g" configs/config.json
sed -i "s/YOUR_PASSWORD/$password/g" configs/config.json
sed -i "s/SOME_LOCATION/$location/g" configs/config.json
sed -i "s/GOOGLE_MAPS_API_KEY/$gmapkey/g" configs/config.json
echo "edit configs/config.json to modify any other config."
}

function Pokebotinstall () {
cd $pokebotpath
echo "1.Debian/Ubuntu"
echo "2.Centos/RedHat"
echo "3.Mac os"
echo "4.Other"
read M
if [ "$M" = "1" ]
then
sudo apt-get update
sudo apt-get -y install python python-pip python-dev build-essential git python-protobuf virtualenv 
elif [ "$M" = "2" ]
then
sudo yum -y install epel-release
sudo yum -y install python-pip
elif [ "$M" = "3" ]
then
sudo brew update 
sudo brew install --devel protobuf
else
echo "Nothing happend."
fi
sudo pip install virtualenv
Pokebotupdate
Pokebotencrypt
echo "Install complete."
}

function Pokebotreset () {
cd $pokebotpath
git fetch --all 
git reset --hard origin/dev
Pokebotupdate
}

function Pokebotrun () {
while true
do
cd $pokebotpath
python pokecli.py -cf ./configs/"$filename"
read -p "Press any button or wait 20 seconds." -r -s -n1 -t 20
echo `date`"Pokebot"$*" Stopped." 
done
}

function Pokebothelp () {
echo "usage:"
echo "	*.json.	    	run Pokebot with *.json."
echo "	-i,-install.	Install PokemonGo-Bot."
echo "	-b,-backup.	    Backup config files."
echo "	-c,-config. 	Easy config generator."
echo "	-e,-encrypt. 	Make encrypt.so."
echo "	-r,-reset.  	Force sync dev branch."
echo "	-u,-update. 	Command git pull to update."
}

case $* in
-install|-i)
Pokebotinstall
;;
-encrypt|-e)
Pokebotencrypt
;;
-reset|-r)
Pokebotreset
;;
-update|-u)
Pokebotupdate
;;
-backup|-b)
mkdir $backuppath
cp -f $pokebotpath/configs/config*.json $backuppath/
cp -f $pokebotpath/web/config/userdata.js $backuppath/
;;
-config|-c)
Pokebotconfig
;;
-help|-h)
Pokebothelp
;;
*.json)
filename=$*
cd $pokebotpath
if [ ! -f ./configs/"$filename" ]
then
echo "There's no ./configs/"$filename" file. use -config to creat one."
else
Pokebotrun
fi
;;
*)
Pokebothelp
;;
esac
exit 0
