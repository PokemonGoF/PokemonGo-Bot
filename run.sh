#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
auth=""
config=""
if [ ! -z $1 ]; then
auth=$1
else
auth="./configs/auth.json"
fi
if [ ! -z $2 ]; then
config=$2
else
config="./configs/config.json"
fi
cd $pokebotpath
source bin/activate
git fetch -a
if [ "1" == $(git branch -vv |grep -c "* dev") ] && [ $(git log --pretty=format:"%h" -1) != $(git log --pretty=format:"%h" -1 origin/dev) ]
then
echo "Branch dev have an update. Run ./setup.sh -u to update."
sleep 2
elif [ "1" == $(git branch -vv |grep -c "* master") ] && [ $(git log --pretty=format:"%h" -1) != $(git log --pretty=format:"%h" -1 origin/master) ]
then
echo "Branch master have an update. Run ./setup.sh -u to update."
sleep 2
fi
if [ ! -f "$auth" ]; then
echo "There's no auth file. Please use ./setup.sh -a to create one"
fi
if [ ! -f "$config" ]; then
echo "There's no config file. Please use ./setup.sh -c to create one."
fi
while true
do
python pokecli.py -af $auth -cf $config
echo `date`" Pokebot "$*" Stopped."
read -p "Press any button or wait 20 seconds to continue.
" -r -s -n1 -t 20
done
exit 0
