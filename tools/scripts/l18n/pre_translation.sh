#!/bin/bash

# Install Python Packages & activate virtual env
python3 -m venv extract-strings-env
source extract-strings-env/bin/activate
pip3 install -r requirements.txt

# Extract API Strings
source extract-strings-env/bin/activate && python3 manage.py makemessages -l en --ignore "extract-strings-env/*"

# Move files to translations folder
mv pinakes/locale/en/LC_MESSAGES/django.po translations/

# cleanup
rm -rf extract-strings-env
