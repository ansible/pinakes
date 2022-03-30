**Developer Setup**
Pinakes has dependencies on Keycloak for Authentication and Authorization.
So in order to test the product you would need Keycloak installed. To overcome
this dependency issue we have provided a minikube/docker/vagrant environment where
you can test the whole product suite. There is separate documentation for
creating and managing those environments. For each of these environments you can
make local changes and test those changes in these environments before submitting
a PR.

A developer can do the following things locally

* Run tests using pytest
* Make code changes, create PR, lint and format the code.
* Create localization files
* To test your changes you can use the minikube/docker/vagrant env.

## Dev Setup

* Pre Requisites
   Python 3.8 needs to be installed in your dev box
* Create a Virtual Environment
   ```python3 -m venv venv```
* Activate the Virtual Enviornment
    ```source venv/bin/activate```
* Clone this repository
     ```
     git clone https://github.com/ansible/pinakes
     cd pinakes
     ```
* Install all the dependencies
     ```
        pip install -r requirements.txt -r dev-requirements.txt -r test-requirements.txt
     ```
* Setup the development settings file, and a secret for the database
```
export DJANGO_SETTINGS_MODULE=pinakes.settings.development
export PINAKES_SECRET_KEY=abcdef
```
   You can override the Database and Tower information in your local development settings file.
   This settings file should not be checked into github, local settings file name should have a prefix of  **local_** e.g.   **pinakes/settings/local_info.py**


* After you have tested in the dev environment you can deactivate the virtual env by using
```deactivate```


* The default database for development is SQLite, you can configure the following environment variables to setup your Postgres DB information

	* PINAKES_POSTGRES_USER (default: catalog)
	* PINAKES_POSTGRES_PASSWORD (default: password)
	* PINAKES_POSTGRES_HOST (default: postgres)
	* PINAKES_POSTGRES_PORT (default: 5432)
	* PINAKES_DATABASE_NAME (default: catalog)


### To run pytest with code coverage
```
pytest --cov=./ --cov-report=html
open htmlcov/index.html
```

### To run localization
```
python3 manage.py makemessages -l en --ignore "venv/*"
```
