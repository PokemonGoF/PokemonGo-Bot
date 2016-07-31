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

while [ 1 ]; do  # Always run, if something goes wrong, just run again...
    python pokecli.py --config ${config}
    sleep 30
done
