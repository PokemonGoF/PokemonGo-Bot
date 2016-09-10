#!/usr/bin/env bash

if [ ! -z "$1" ]; then
    port="$1"
else
    port="8000"
fi

cd web
python -m SimpleHTTPServer "$port"
