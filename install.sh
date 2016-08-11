#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
cd $pokebotpath
if [ -f /etc/debian_version ]
then
echo "You are on Debian/Ubuntu"
sudo apt-get update
sudo apt-get -y install python python-pip python-dev build-essential git python-protobuf virtualenv 
elif [ -f /etc/redhat-release ]
then
echo "You are on CentOS/RedHat"
sudo yum -y install epel-release
sudo yum -y install python-pip
elif [ "$(uname -s)" == "Darwin" ]
then
echo "You are on Mac os"
sudo brew update 
sudo brew install --devel protobuf
else
echo "Please check if you have  python pip protobuf gcc make  installed on your device."
echo "Wait 5 seconds to continue or Use ctrl+c to interrupt this shell."
sleep 5
fi
pip install virtualenv
cd $pokebotpath
git pull
git submodule init
git submodule foreach git pull origin master
virtualenv .
source bin/activate
pip install -r requirements.txt
echo "Start to make encrypt.so"
wget http://pgoapi.com/pgoencrypt.tar.gz
tar -xf pgoencrypt.tar.gz 
cd pgoencrypt/src/ 
make
mv libencrypt.so $pokebotpath/encrypt.so
cd ../..
rm -rf pgoencrypt.tar.gz
rm -rf pgoencrypt
echo "Install complete. Starting to generate config.json."
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
echo "Edit configs/config.json to modify any other config. Use run.sh ./configs/config.json to run."
exit 0
