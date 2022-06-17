# Change Directory to clones
cd _clones

# Extract API Strings
source extract-strings-env/bin/activate && python3 manage.py makemessages -l en --ignore "extract-strings-env/*"

# Move files to translations folder
mv /locale/en/LC_MESSAGES/django.po /translations/
