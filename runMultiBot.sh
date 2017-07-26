#!/usr/bin/env bash
pokebotpath=$(cd "$(dirname "$0")"; pwd)
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
required=(`cat requirements.txt | sed -e 's/.*pgoapi$/pgoapi==1.2.0/' -e 's/[-_]//g' -e 's/==\(.*\)/:\1/' | awk '{print tolower($0)}'`)
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
python MultiBot.py
done
exit 0
