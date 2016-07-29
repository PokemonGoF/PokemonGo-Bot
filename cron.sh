#!/bin/bash
FILES=$(ls ./configs/*.json | grep -v example)
for f in $FILES
do
    f="$(echo $f | cut -d'/' -f3)"
    let proc_count="$(ps x | grep -v grep | grep pokecli.py | grep $f | grep -c .)"
    if [[ $proc_count -lt 1 ]]; then
	NAME="$(echo $f | cut -d'.' -f 1)"
	screen -S $NAME -dm python pokecli.py -cf "./configs/$f"
    fi
done