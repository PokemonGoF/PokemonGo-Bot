#!/bin/bash
echo "Desenvolvido por Guilherme:)"
echo "----------------------------------------------------------"
sudo apt-get install python-dev 
sudo apt-get install python-virtualenv
sudo virtualenv .
source bin/activate
sudo pip install -r requirements.txt
echo "---------------------"
wget http://pgoapi.com/pgoencrypt.tar.gz
tar -xf pgoencrypt.tar.gz
cd pgoencrypt/src/ 
make
sudo mv libencrypt.so ../../encrypt.so
cd ..
cd ..
cd configs/
sudo cp config.json.bak  config.json
echo "configuring ......"
echo "----------------------"
echo "Enter with you ptc login: "
read ptcLog
echo "-----------------------"
echo "Enter with your ptc password: "
read -s ptcPass
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
sudo sed 's/3/'$ptcLog'/g' config.json > configG.json
sudo mv configG.json config.json
sudo sed 's/4/'$ptcPass'/g' config.json > configU.json
sudo mv configU.json  config.json
sudo sed 's/6/'$loct'/g' config.json > configI.json
sudo mv configI.json  config.json
sudo sed 's/5/'$gpi'/g' config.json > configL.json
sudo mv configL.json  config.json
echo "almost finish ....."
echo "Capturing your mom BrHu3"
echo "-------------------------"
cd ..
./run.sh
