#!/bin/bash
while (true)
do
virtualenv .
pip install -r requirements.txt
python pokecli.py
echo 'Bot will reinitiated in 60 seconds'
echo -ne '#  \r'
sleep 3
echo -ne '## \r'
sleep 3
echo -ne '#### \r'
sleep 3
echo -ne '##### \r'
sleep 3
echo -ne '###### \r'
sleep 3
echo -ne '####### \r'
sleep 3
echo -ne '######## \r'
sleep 3
echo -ne '######### \r'
sleep 3
echo -ne '########## \r'
sleep 3
echo -ne '########### \r'
sleep 3
echo -ne '############ \r'
sleep 3
echo -ne '############# \r'
sleep 3
echo -ne '############## \r'
sleep 3
echo -ne '############### \r'
sleep 3
echo -ne '################ \r'
sleep 3
echo -ne '################# \r'
sleep 3
echo -ne '################## \r'
sleep 3
echo -ne '################### \r'
sleep 3
echo -ne '#################### \r'
sleep 3
echo -ne '##################### \r'
echo -ne '\n'

done
