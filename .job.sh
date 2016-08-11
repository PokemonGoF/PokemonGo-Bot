#!/bin/sh
while true
do
    gtimeout 3600 python pokecli.py -cf ./configs/config.json
done
