#!/bin/bash
cd ..
while true
do
  ./pokecli.py -cf $1
  echo ">pokecli exited... restarting...";
  sleep 5;
done
