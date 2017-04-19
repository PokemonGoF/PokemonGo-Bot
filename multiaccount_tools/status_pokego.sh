#! /bin/bash
ps -C python -o pid,args | grep pokecli | grep configName1 > /dev/null && echo configName1 is running || echo configName1 is stopped
ps -C python -o pid,args | grep pokecli | grep configName2 > /dev/null && echo configName2 is running || echo configName2 is stopped
ps -C python -o pid,args | grep pokecli | grep configName3 > /dev/null && echo configName3 is running || echo configName3 is stopped
