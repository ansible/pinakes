# INSTALL
How to install ansible catalog in a production-like environment. This guide assumes a basic knowledge about networking and systems administration. 

## Components
- Backend: django application for the REST api
- Frontend: react application for the UI client
- Workers: async workers
- Scheduler: async worker to run scheduled tasks
- Database: postgres database for backend and workers
- Broker: redis database for the workers
- Keycloak: provider for authentication and authorization

![arch overview](./docs/catalog-arch.png?raw=true)

## Dependencies
Ansible Catalog acts as a client for the ansible controller (AKA ansible tower). It can work without connectivity to the controller with limited functionality. 

## Requirements
- Python >= 3.6
- Postgresql >= 13
- Redis >= 6.0
- Static file web server  (AWS S3, nginx, etc...)
- Keycloak >= 15

## How to install
Note: all command examples are based on a clean linux server with a RHEL compatible OS. Please check the respective official documentation for the equivalent commands if you use another environment. 

### Keycloak
Install Keycloak and configure credentials for the admin user. See the official docs for further information

### Postgres
Install postgres and create a database and a user with all permissions over that database. See the official docs for further information

### Redis
Install redis, the default values are enough. See the official docs for further information

### First steps

- Install python:
```
yum install -y python3
```

- You may need to install `python3-psycopg2` package and the latest version of pip:
```
yum install -y python3-psycopg2
pip3 install -U pip
```

### Keycloak setup
Several configurations must be done in keycloak in order to be used by ansible catalog as auth provider. There is an ansible collection to do it automatically. There are some variables that must be configured for the ansible collection in `tools/keycloak_setup/dev.yml`
Copy this file and modify `seed_users` according to your setup and needs. 

- install ansible and the collection:
```
pip3 install ansible
ansible-galaxy collection install community.general mkanoor.catalog_keycloak
```

- some environment variables are needed: 
```
# internal keycloak url
export AUTOMATION_SERVICES_CATALOG_KEYCLOAK_URL=http://keycloak:8080/auth

# keycloak client secret configured (see keycloak setup ahead)
export AUTOMATION_SERVICES_CATALOG_KEYCLOAK_CLIENT_SECRET=SOMESECRETVALUE

# keycloak admin user
export AUTOMATION_SERVICES_CATALOG_KEYCLOAK_USER=admin

# keycloak admin password
export AUTOMATION_SERVICES_CATALOG_KEYCLOAK_PASSWORD=password

# public keycloak url
export AUTOMATION_SERVICES_CATALOG_KEYCLOAK_REALM_FRONTEND_URL=http://keycloak.k8s.local/auth

# comma separated values of the internal django urls that keycloak will use for internal redirects
export REDIRECT_URIS_STR=http://app:8000,http://app:8000/*,*
```

- run the collection:
```
ansible-playbook [path to your custom conf, eg: tools/keycloak_setup/dev.yml]
```


### Backend, worker and scheduler
- clone source code:
```
git clone https://github.com/ansible/ansible-catalog.git
```


- Install python dependencies
```
pip3 install -r requirements.txt
```

_Note_: _All application settings are defined in `automation_services_catalog/settings/defaults.py`. If you prefer to use a configuration file instead of environment variables you can modify this file. Also you can create your own file but you have to configure the environment variable `DJANGO_SETTINGS_MODULE`._


- The following environment variables must to be configured:

```
# WARNING: all these values are examples taken from the development environment, don't use it in your installation!


# postgres conf
export AUTOMATION_SERVICES_CATALOG_DATABASE_NAME=dev_catalog
export AUTOMATION_SERVICES_CATALOG_POSTGRES_HOST=postgres
export AUTOMATION_SERVICES_CATALOG_POSTGRES_USER=postgres
export AUTOMATION_SERVICES_CATALOG_POSTGRES_PASSWORD=password

# path where are stored the media files (basically images)
export AUTOMATION_SERVICES_CATALOG_MEDIA_ROOT=/app/media

# secret key for internal cryptographic tasks. You can generate it here: https://djecrety.ir/
export AUTOMATION_SERVICES_CATALOG_SECRET_KEY="django-insecure-k8^atj4p3jj^zkb3=o(rhaysjzy_mr&#h(yl+ytj#f%@+er4&5"

# internal ansible controller configuration
export AUTOMATION_SERVICES_CATALOG_CONTROLLER_URL=http://172.0.2.3
export AUTOMATION_SERVICES_CATALOG_CONTROLLER_TOKEN=somesecrettoken
export AUTOMATION_SERVICES_CATALOG_CONTROLLER_VERIFY_SSL=true
```

- The following environment variables are optional
```
# enable debug mode for django
export AUTOMATION_SERVICES_CATALOG_DEBUG=False

# internal redis conf
export AUTOMATION_SERVICES_CATALOG_REDIS_HOST=localhost
export AUTOMATION_SERVICES_CATALOG_REDIS_PORT=6379
export AUTOMATION_SERVICES_CATALOG_REDIS_DB=0

# use it to define a custom configuration file as python module syntax 
export DJANGO_SETTINGS_MODULE=automation_services_catalog.settings.defaults

# comma separated allowed public hostnames for the backend
export AUTOMATION_SERVICES_CATALOG_ALLOWED_HOSTS=*

# enable if the application is served under https (recommended)
export AUTOMATION_SERVICES_CATALOG_HTTPS_ENABLED=True

# public hostname [scheme]://[hostname] where the application is served, it can be a list of comma separated values
export AUTOMATION_SERVICES_CATALOG_CSRF_TRUSTED_ORIGINS=https://[your-public-hostname]
```

- Run the backend:

**migrate and collectstatic commands must be executed with each application update**
```
# ensure correct state for database
python manage.py migrate

# generate static files for backend
python manage.py collectstatic

# run the backend
gunicorn --workers=3 --bind 0.0.0.0:8000 automation_services_catalog.wsgi --log-level=info
```

- Run the worker
```
python manage.py rqworker default
```

- Run the scheduler
```
python manage.py cronjobs
```

### Frontend
A static file webserver must be configured to serve the UI application, backend's static files and media files. NGINX is a good choice and the webserver recommended for this guide. See the official docs for further information.

You can find an example of the required configuration for the NGINX in `tools/minikube/nginx/catalog-nginx.conf`

The latest build of the UI can be downloaded from the releases page in the oficial repository: 

https://github.com/RedHatInsights/catalog-ui/releases

Download and unpack the UI build and modify the nginx configuration for the right directories and server names. 

NOTE: The UI must be served under the same public hostname as the backend. 




