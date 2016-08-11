#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
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
echo `date`" Pokebot "$*" Stopped." 
read -p "Press any button or wait 20 seconds to continue.
" -r -s -n1 -t 20
done
exit 0
