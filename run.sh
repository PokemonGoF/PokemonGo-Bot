#!/usr/bin/env bash

# Starts PokemonGo-Bot
config=""

if [ ! -z $1 ]; then
    config=$1
else
    config="./configs/config.json"
    if [ ! -f ${config} ]; then
        echo -e "There's no ./configs/config.json file"
        echo -e "Please create one or use another config file"
        echo -e "./run.sh [path/to/config/file]"
        exit 1
    fi
fi

while [ true  ]
do
echo "###############################################"
echo "##Exit two times with [Ctl+C] to end the loop##"
echo "###############################################"
sleep 1
python pokecli.py --config ${config}
sleep "10"
done
