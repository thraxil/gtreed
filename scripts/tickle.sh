#!/bin/bash
export PYTHON_EGG_CACHE=/home/anders/code/python/TreeD/.python-eggs
cd $1
source working-env/bin/activate
exec python scripts/tickle.py
