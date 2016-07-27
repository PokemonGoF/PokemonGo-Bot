#! /bin/bash

echo 'killing all running bots(just in case)...'
echo 
./stop_pokego.sh


echo
echo 'starting bots in separate screen sessions...'
echo
screen -dmS screenName1 ./loop.sh configs/configName1.config && echo username1 started
screen -dmS screenName2 ./loop.sh configs/configName2.config && echo username2 started
screen -dmS screenName3 ./loop.sh configs/configName3.config && echo username3 started
#copy/remove the line above to add/remove bots


#start http server on localhost:8080

cd ../web
screen -dmS server_pokemon python -m SimpleHTTPServer 8080 && echo server http started
