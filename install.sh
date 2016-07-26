#!/usr/bin/env bash

# Setup Python virtualenv
echo "Setting up Python virtualenv..."
eval "virtualenv ."
eval "source bin/activate"
echo "Python virtualenv setup successfully."

# Install pip requirements
echo "Installing pip requirements..."
eval "pip install -r requirements.txt"
echo "Installed pip requirements."
echo "Installing and updating git submodules..."

# Install git submodules
eval "cd ./web && git submodule init && cd .."
eval "git submodule update"
echo "Done."
echo "Please create and setup configs/config.json. Then, run 'python pokecli.py --config ./configs/config.json' or './run.sh' on Mac/Linux"