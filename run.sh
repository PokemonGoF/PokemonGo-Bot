#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
auth=""
config=""
if [ ! -z $1 ]; then
  config=$1
else
  config="./configs/config.json"
fi
if [ ! -z $2 ]; then
  auth=$2
else
  auth="./configs/auth.json"
fi
cd $pokebotpath
source bin/activate 2> /dev/null
if [[ $? -eq 1 ]];
then
  echo "Virtualenv does not exits"
  echo "Run: ./setup.sh -i"
  exit 1
fi
git fetch -a
installed=(`pip list 2>/dev/null |sed -e 's/ //g' -e 's/(/:/' -e 's/)//' -e 's/[-_]//g' | awk '{print tolower($0)}'`)
required=(`cat requirements.txt | sed -e 's/.*pgoapi$/pgoapi==2.13.0/' -e 's/[-_]//g' -e 's/==\(.*\)/:\1/' | awk '{print tolower($0)}'`)
for package in ${required[@]}
do
  if [[ ! (${installed[*]} =~ $package) ]];
  then
    echo "Some of the required packages are not found / have different version."
    echo "Run: ./setup.sh -u"
    exit 1
  fi
done
if [ "1" == $(git branch -vv |grep -c "* dev") ] && [ $(git log --pretty=format:"%h" -1) != $(git log --pretty=format:"%h" -1 origin/dev) ] ||
  [ "1" == $(git branch -vv |grep -c "* master") ] && [ $(git log --pretty=format:"%h" -1) != $(git log --pretty=format:"%h" -1 origin/master) ]
then
  read -p "Branch has an update. Run ./setup.sh -u to update? y/n
  " do_setup
  if [[ $do_setup = "y" || $do_setup = "Y" ]];
  then
    ./setup.sh -u
  fi
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
