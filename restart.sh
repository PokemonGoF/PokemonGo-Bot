#!/bin/bash
kill -9 $(ps xw | grep -v grep | grep pokecli | grep -v -i screen | awk {'print $1'} | xargs)
screen -wipe >> /dev/null 2>&1

