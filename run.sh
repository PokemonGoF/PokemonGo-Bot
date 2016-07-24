#!/bin/bash
set -e

echo "====================="
echo "Updating requirements"
echo "====================="

pip install -r requirements.txt

echo "====================="
echo "Update sucessful!"
echo "====================="

exec python pokecli.py "$@"
