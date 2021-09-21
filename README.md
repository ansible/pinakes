

# Ansible Catalog

Ansible Catalog allows customers to expose their Ansible Job Templates and Workflows to business users with an added layer of governance. The Job Templates and Workflows are wrapped as Products into Portfolios which can be shared with different business users. An approval workflow can be attached to Products or Portfolios which adds governance and, in the future, will be able to notify the appropriate Administrators via email. Upon approval, the Job Template or workflow will be launched on the Ansible Controller.

Ansible Catalog in the future will also support editing of Survey Specs to create different flavors of the Job Template or Workflow with pre-canned parameters so businesss users don't have to be concerned about the details of a parameter.


For Authentication and Authorization Ansible Catalog uses [Keycloak](https://github.com/chambridge/galaxy_ng/tree/poc-keycloak-py-social). Keycloak can be configured to use a customers LDAP Server.


Ansible Catalog runs on-prem alongside the Ansible Controller and communicates with it over REST APIs. The product is broken up into 3 main areas

 1. Catalog, deals with the creation of Products, Portfolios and Orders
 2. Approval, deals with the Approval process and notifications
 3. Inventory, deals with connecting to the Ansible Controller using REST API to fetch objects and launch Ansible Controller Jobs.

![Alt UsingUploadService](./docs/ansible_catalog.png?raw=true)


**Developer Setup**
* Pre Requisites 
   Python 3.8 needs to be installed in your dev box
* Create a Virtual Environment
   ```python3 -m venv venv```
* Activate the Virtual Enviornment
    ```source venv/bin/activate```
* Clone this repository
     ```
     git clone https://github.com/ansible/ansible-catalog
     cd ansible-catalog
     ```
 * Install all the dependencies
     ```pip install -r requirements.txt```
 * Prep the Database (Sqlite by default ansible_catalog/catalog.db)
 ```
      python3 manage.py migrate
      python3 manage.py createsuperuser
```
* Check for the existence of the log directory, by default we log to /var/log/ansible_catalog/ if you don't have access to this directory. You can use an environment variable CATALOG_LOG_ROOT and set it to the the directory that exists and you have access to e.g.
  ```export CATALOG_LOG_ROOT=/tmp```    
* Setup the development settings file
```
export DJANGO_SETTINGS_MODULE=ansible_catalog.settings.development
```
   You can override the Database and Tower information in your local development settings file.
   This settings file should not be checked into github, local settings file name should have a prefix of  **local_** e.g.   **ansible_catalog/settings/local_info.py**
   
   To store tower info use the following keys
   
  * CONTROLLER_TOKEN="Your Token"
  * CONTROLLER_URL="Your Controller URL"
  * CONTROLLER_VERIFY_SSL="False"
  
* Start the Server using development settings
      ```python3 manage.py runserver```
      
      Open your browser and open http://127.0.0.1:8000/catalog/api/v1/portfolios/
      
      When prompted provide the userid/password from the createsuperuser step

* After you have tested in the dev environment you can deactivate the virtual env by using
```deactivate```
* (Optional) The default database for development is SQLite but you can change it to use PostgreSQL by configuring your database information in the **ansible_catalog/settings/local_info.py** settings file.
```
DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.postgresql_psycopg2",
    "NAME":"<<your_db_name>>",
    "USER":"<<your_db_user>>",
    "PASSWORD":"<<your_db_password>>",
    "HOST":"<<your_db_host>>",
    "PORT":"5432",
  }
}
```
* To run background tasks we use Django RQ, which has a dependency on Redis. You would have to install Redis locally on your dev box. To start the redis worker locally use the following command
```redis-server /usr/local/etc/redis.conf```
* To run a worker to handle the background tasks we need to run the worker separate from the server.
  ```
  #!/bin/sh
  export CATALOG_ROOT_URL=/tmp
  export DJANGO_SETTINGS_MODULE=ansible_catalog.settings.development
  # This is needed only on Mac OS
  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
  python3 manage.py rqworker default
  ```
## Local Container ##
### Requirements
You will need to install docker/podman and docker-compose. 


#### previous steps for podman
You must first init the api socket for podman:
```
# only linux 
systemctl --user enable --now podman.socket
```

And also export the socket:

```
# only linux 
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock
```

### Build and Run

```
cd tools/docker-compose
```

Build the containers
```
docker-compose build
```

Run the application
```
docker-compose up
```

Now you can try to open http://localhost:8000/api/v1/
The project path is mounted in the pod and you can edit it in real time from outside the container. 

You can get an interactive shell inside the application pod with the command:
```
docker-compose exec app bash
```

### Things to do manually the first time
- create a superuser:
```
docker-compose exec app python manage.py createsuperuser
```

- create the source: (Ensure before you have configured the tower connection, see above)
```
docker-compose exec app python manage.py shell
>>> from main.models import Source, Tenant
>>> Source.objects.create(name="source_1", tenant=Tenant.current())
```
open in your browser: http://localhost:8000/api/v1/sources/1/refresh/
and execute a patch with empty body. (this may take a while)

### Generate the open api specfile
```
docker-compose exec app python manage.py spectacular --format openapi-json --file apispec.json
```
## Using minikube for development
###  Setup minikube
[Install minikube](https://minikube.sigs.k8s.io/docs/start/)
Start minikube
Since the catalog, keycloak, postgres, redis all run inside the minikube cluster we need to expose the catalog and keycloak services from the cluster to your local dev machine using ingress. We need to enable ingress on the minikube cluster

```
minikube addons enable ingress
```

 [More on that here](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)

Get the IP address of the minikube cluster
```
minikube ip
```

The ingress uses 2 hardcoded hosts **catalog.test** and **keycloak.test** to route the traffic to the appropriate services so we need to add the the IP address from the above command into /etc/hosts. The /etc/hosts should have this line 
```
<<ip_from_minikube_ip>> catalog.test keycloak.test
```
## Building the image

```
minikube image build -t localhost/ansible-catalog -f tools/minikube/Dockerfile .
```

## Starting the app
Once this has been setup you can start the deployments, services and ingress service in the directory minikube_files

```
cd tools/minikube/minikube_files
kubectl apply -f .
```

To access the keycloak server running inside the cluster use the following URL
http://keycloak.test/auth  (Default userid is admin password is admin)
To access the catalog app use
http://catalog.test/api/v1/

When the catalog-app starts up it creates the required roles, policies, scopes, permissions (optionally groups and users) by using an ansible collection. The roles, policies, scopes and permissions are defined in the collection. The optional group and user data is stored in keycloak_setup/dev.yml
 
As part of the keycloak setup we create the following groups

 - **catalog-admin**
 - **catalog-user**
 - **approval-admin**
 - **approval-user**
 - **approval-approver**

The following users are also created

 - **fred** (member of catalog-admin, approval-admin)
 - **barney** (member of catalog-user, approval-user)
 - **wilma** (member of approval-approver)

The default password is the same as the user name, they can be changed by modifying the file **keycloak_setup/dev.yml**
