#!/bin/bash

# Rename the zh_cn folder 
mv translations/zh_cn translations/zh

# Create a directory for api (locale)
mkdir locale

# Copy all subdirectories to locale
cp -r translations/ locale/

# Loop over each directory and create another directory LC_Messages
# Move django.po & django.mo files to LC_Messages
cd locale/
for d in */ ; do
    dir=${d%*/}
    mkdir $dir/LC_MESSAGES
    mv $dir/django.po $dir/LC_MESSAGES/
done

cd ..

pinakes_api_path="pinakes/locale" # locale will be dropped here

rsync -av locale/ $pinakes_api_path

# Install Python Packages & activate virtual env
python3 -m venv extract-strings-env
source extract-strings-env/bin/activate
pip3 install -r requirements.txt

# Set temporary/ random secret key for pinakes
export PINAKES_SECRET_KEY=$RANDOM  

# Extract MO String
python3 manage.py compilemessages --ignore "extract-strings-env/*" --ignore "venv/*"

# # cleanup
rm -rf extract-strings-env
rm -rf translations/
rm -rf locale/
