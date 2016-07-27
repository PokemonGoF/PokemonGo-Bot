#! /bin/bash
ps -C screen -o pid,args | grep loop | grep configName1 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName1 killed
ps -C screen -o pid,args | grep loop | grep configName2 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName2 killed
ps -C screen -o pid,args | grep loop | grep configName3 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName3 killed
ps -C screen -o pid,args | grep SimpleHTTP | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo http server killed
