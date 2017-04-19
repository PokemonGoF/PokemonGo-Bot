#! /bin/bash
ps -C python -o pid,args | grep pokecli | grep configName1 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName1 killed
ps -C python -o pid,args | grep pokecli | grep configName2 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName2 killed
ps -C python -o pid,args | grep pokecli | grep configName3 | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo configName3 killed
ps -C python -o pid,args | grep SimpleHTTP | sed -n 's/ *\([0-9][0-9]*\).*/\1/p' | xargs kill 2> /dev/null && echo http server killed
