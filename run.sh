#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
filename=""
if [ ! -z $1 ]; then
filename=$1
else
filename="./configs/config.json"
fi
cd $pokebotpath
source bin/activate
if [ ! -f "$filename" ]; then
echo "There's no "$filename" file. Please use ./setup.sh -c to creat one."
fi
while true
do
python pokecli.py -cf $filename
echo `date`" Pokebot "$*" Stopped." 
read -p "Press any button or wait 20 seconds to continue.
" -r -s -n1 -t 20
done
exit 0
