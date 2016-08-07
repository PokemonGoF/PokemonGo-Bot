#!/bin/bash
echo "Desenvolvido por Guilherme:) www.facebook.com/guilhermexyz"
echo "----------------------------------------------------------"
sudo su
apt-get install python-dev 
apt-get install python-virtualenv
virtualenv .
source bin/activate
pip install -r requirements.txt
echo "KUdS API initialized...."
echo " by guilherme"
echo "---------------------"
wget http://pgoapi.com/pgoencrypt.tar.gz
tar -xf pgoencrypt.tar.gz
cd pgoencrypt/src/ 
make
mv libencrypt.so ../../encrypt.so
cd ..
cd ..
cd configs/
cp config.json.bak  config.json
echo "configuring ......"
echo "----------------------"
echo "Enter with you ptc login: "
read ptcLog
echo "-----------------------"
echo "Enter with your ptc password: "
read ptcPass
echo "------------------------"
echo "Enter With your GoogleMaps API Key: "
echo "   [+] Get one here > https://developers.google.com/maps/documentation/javascript/get-api-key"
read gpi
echo "------------------------"
echo " Enter with your location: "
echo " [+] Example: -22.9314839,-45.4561115"
echo "    [+] Get in www.google.com/maps, inser your postal code and get the latitude in url"
read loct
echo "-------------------------"
sed 's/3/'$ptcLog'/g' config.json > configG.json
mv configG.json config.json
sed 's/4/'$ptcPass'/g' config.json > configU.json
mv configU.json  config.json
sed 's/6/'$loct'/g' config.json > configI.json
mv configI.json  config.json
sed 's/5/'$gpi'/g' config.json > configL.json
mv configL.json  config.json
echo "almos finish ....."
echo "Capturing your mom BrHu3"
echo "-------------------------"
cd ..
./run.sh
