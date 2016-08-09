#!/usr/bin/env bash
pokebotpath=$(pwd)
filename=$*
cd $pokebotpath
if [ ! -f ./configs/"$filename" ]
then
echo "There's no ./configs/"$filename" file. use setup.sh -config to creat one."
else
while true
do
cd $pokebotpath
python pokecli.py -cf ./configs/"$filename"
read -p "Press any button or wait 20 seconds." -r -s -n1 -t 20
echo `date`"Pokebot"$*" Stopped." 
done
fi
exit 0
