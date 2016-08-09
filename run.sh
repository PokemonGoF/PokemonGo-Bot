#!/usr/bin/env bash
pokebotpath=$(pwd)
filename=""
if [ ! -z $1 ]; then
filename=$1
else
filename="./configs/config.json"
fi

if [ ! -f "$filename" ]; then
echo "There's no "$filename" file. use setup.sh -config to creat one."
fi

while true
do
cd $pokebotpath
python pokecli.py -cf $filename
read -p "Press any button or wait 20 seconds." -r -s -n1 -t 20
echo `date`"Pokebot"$*" Stopped." 
done
exit 0
