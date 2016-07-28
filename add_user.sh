#!/bin/bash
if [[ $# -lt 1 ]]; then
    echo "Illegal number of parameters"
    echo "./add_user user1 user2 user...n"
    echo 'The filename ./configs/config_user.json.example that contains all settings and "username": "MY_USERNAME", is required'
    exit
fi

for user in "$@"; do
    cp ./configs/config_user.json.example "./configs/$user.json"
    sed -i "s/MY_USERNAME/$user/g" "./configs/$user.json"
    sed -i "s/var users = \[/var users = \[\"$user\", /g" web/userdata.js
    echo "$user"
done