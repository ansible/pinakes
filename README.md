


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

      Open your browser and open http://127.0.0.1:8000/api/ansible-catalog/v1/portfolios/

      When prompted provide the userid/password from the createsuperuser step

* After you have tested in the dev environment you can deactivate the virtual env by using
```deactivate```
* The default database for development is Postgres, you can configure the following environment variables to setup your Postgres DB information

	* ANSIBLE_CATALOG_POSTGRES_USER (default: catalog)
	* ANSIBLE_CATALOG_POSTGRES_PASSWORD (default: password)
	* ANSIBLE_CATALOG_POSTGRES_HOST (default: postgres)
	* ANSIBLE_CATALOG_POSTGRES_PORT (default: 5432)
	* ANSIBLE_CATALOG_DATABASE_NAME (default: catalog)

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
## Using docker-compose for development
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

Build the containers (docker)
```
cd tools/docker/
docker-compose build
```
Build the containers (rootless podman)
```
cd tools/docker/
docker-compose build --build-arg USER_ID=0
```


Run the application (this may take a while until the keycloak setup process has finished)
```
docker-compose up -d
```

Now you can try to open http://localhost:8000/api/ansible-catalog/v1/
You can do log in with http://localhost:8000/login/keycloak/
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
>>> from ansible_catalog.main.models import Source, Tenant
>>> Source.objects.create(name="source_1", tenant=Tenant.current())
```
open in your browser: http://localhost:8000/api/ansible-catalog/v1/sources/1/refresh/
and execute a patch with empty body. (this may take a while)

### Download the open api schema
http://localhost:8000/api/ansible-catalog/v1/schema/openapi.json


### Try with swagger UI
http://localhost:8000/api/ansible-catalog/v1/schema/swagger-ui/


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

The ingress uses 2 hardcoded hosts **catalog** and **keycloak** to route the traffic to the appropriate services so we need to add the the IP address from the above command into /etc/hosts. The /etc/hosts should have this line
```
<<ip_from_minikube_ip>> catalog.k8s.local keycloak.k8s.local
```
## Building the image

```
minikube image build -t localhost/ansible-catalog -f tools/docker/Dockerfile .
```
## Starting the app
Once this has been setup you can start the deployments, services and ingress service in the directory tools/minikube/templates. A helper script creates a Kubernetes namespace called **catalog** and runs all the deployments in that namespace. The helper scripts requires 3 environment variables to locate the Automation Controller.
  - **export ANSIBLE_CATALOG_CONTROLLER_URL="Your controller url"**
  - **export ANSIBLE_CATALOG_CONTROLLER_TOKEN="Your Token"**
  - **export ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL="False"**

```
./tools/minikube/scripts/start_pods.sh
```

To login to the UI use
http://catalog.k8s.local/ui/index.html

To access the keycloak server running inside the cluster use the following URL
http://keycloak.k8s.local/auth  (Default userid is admin password is admin)


To login to the catalog app using API endpoint
http://catalog.k8s.local/login/keycloak-oidc/
When prompted enter the userid/password (barney/barney)
This would lead to a page (http://catalog.k8s.local/accounts/profile/) that has a 404 not found that's ok.

To access the catalog app use

http://catalog.k8s.local/api/ansible-catalog/v1/schema/openapi.json
http://catalog.k8s.local/api/ansible-catalog/v1/portfolios/ (You wont be able to get to this link without logging in first)

### Applying local code changes for testing
To deploy your code changes that you have made locally before creating a PR you can redeploy the app using
```
./tools/minikube/scripts/redeploy_app.sh
```

This will stop the app and worker pods, build the image with latest changes and
start the app and worker pods.

### Starting a fresh with a clean env 
To delete all the pods and reset the application, run the helper_script delete_pods.sh

```
./tools/minikube/scripts/delete_pods.sh
```

## About credentials

When the catalog-app starts up it creates the required roles, policies, scopes, permissions (optionally groups and users) by using an ansible collection. The roles, policies, scopes and permissions are defined in the collection. The optional group and user data is stored in tools/keycloak_setup/dev.yml

For ease of development as part of the keycloak setup we create the following groups

 - **catalog-admin**
 - **catalog-user**
 - **approval-admin**
 - **approval-user**
 - **approval-approver**

The following users are also created

 - **fred** (member of catalog-admin, approval-admin)
 - **barney** (member of catalog-user, approval-user)
 - **wilma** (member of approval-approver)

The default password is the same as the user name, they can be changed by modifying the file **tools/keycloak_setup/dev.yml**


