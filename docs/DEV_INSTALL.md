**Developer Setup**
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
     ```pip install -r requirements.txt```
 * Prep the Database (Sqlite by default pinakes/catalog.db)
 ```
      python3 manage.py migrate
      python3 manage.py createsuperuser
```
* Setup the development settings file, and a secret for the database
```
export DJANGO_SETTINGS_MODULE=pinakes.settings.development
export PINAKES_SECRET_KEY=abcdef
```
   You can override the Database and Tower information in your local development settings file.
   This settings file should not be checked into github, local settings file name should have a prefix of  **local_** e.g.   **pinakes/settings/local_info.py**

   To store tower info use the following keys

  * CONTROLLER_TOKEN="Your Token"
  * CONTROLLER_URL="Your Controller URL"
  * CONTROLLER_VERIFY_SSL="False"

* Start the Server using development settings
      ```python3 manage.py runserver```

      Open your browser and open http://127.0.0.1:8000/api/pinakes/v1/portfolios/

      When prompted provide the userid/password from the createsuperuser step

* After you have tested in the dev environment you can deactivate the virtual env by using
```deactivate```
* The default database for development is Postgres, you can configure the following environment variables to setup your Postgres DB information

	* PINAKES_POSTGRES_USER (default: catalog)
	* PINAKES_POSTGRES_PASSWORD (default: password)
	* PINAKES_POSTGRES_HOST (default: postgres)
	* PINAKES_POSTGRES_PORT (default: 5432)
	* PINAKES_DATABASE_NAME (default: catalog)

* To run background tasks we use Django RQ, which has a dependency on Redis. You would have to install Redis locally on your dev box. To start the redis worker locally use the following command
```redis-server /usr/local/etc/redis.conf```
* To run a worker to handle the background tasks we need to run the worker separate from the server.
  ```
  #!/bin/sh
  export CATALOG_ROOT_URL=/tmp
  export DJANGO_SETTINGS_MODULE=pinakes.settings.development
  python3 manage.py rqworker default
  ```
* To run a scheduler to schedule the background tasks we need to run the scheduler separate from the server. 
  ```
  python manage.py cronjobs  # (re)schedule cron jobs defined in the settings file  
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
Create a terminal session and go in the docker-compose env dir:

```
cd tools/docker/
```

Build the containers (docker)
```
docker-compose build
```

Build the containers (rootless podman)
```
docker-compose build --build-arg USER_ID=0
```

You have to create a .env file with the environments variables for the controller:
```
# .env contents:
PINAKES_CONTROLLER_TOKEN=secret-token
PINAKES_CONTROLLER_URL="https://your-controller-host"
```

Run the application (this may take a while until the keycloak setup process has finished)
```
docker-compose up -d
```

You can check that everything works as expected with
```
docker-compose logs -f
```
(You will see errors in the worker until keycloak is properly configured)

Once is finished you can try to open https://localhost:8443/api/pinakes/v1/
You can do log in with https://localhost:8443/login/keycloak/
You can open the UI with https://localhost:8443/ui/catalog/index.html
The project path is mounted in the pod and you can edit it in real time from outside the container.

You can get an interactive shell inside the application pod with the command:
```
docker-compose exec app bash
```

Remove the deployment (add `-v` flag to remove the volumes as well)
```
docker-compose down
```


### Deploy catalog in a production-like setup:
There is an alternative docker-compose file to deploy the application in a more production-like setup:

```
docker-compose build
docker-compose -f docker-compose.stage.yml up -d
```

You can change the exposed port for stage environment adding the `FRONTEND_HTTPS_PORT` environment variable. Note that using ports under 1024 requires root privileges. In order to use the standard https port (443) you have to add more variables in your `.env` file:

```
FRONTEND_HTTPS_PORT=443
FRONTEND_CONF_PATH=./frontend/nginx-443.conf
```

Deploy it as root (if you work with podman, you have to build the images as root also)
```
sudo docker-compose -f docker-compose.stage.yml up -d
```


### Download the open api schema
http://localhost:8000/api/pinakes/v1/schema/openapi.json


### Try with swagger UI
http://localhost:8000/api/pinakes/v1/schema/swagger-ui/


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
minikube image build -t localhost/pinakes -f tools/docker/Dockerfile .
```
## Starting the app
Once this has been setup you can start the deployments, services and ingress service in the directory tools/minikube/templates. A helper script creates a Kubernetes namespace called **catalog** and runs all the deployments in that namespace. The helper scripts requires 3 environment variables to locate the Automation Controller.
  - **export PINAKES_CONTROLLER_URL="Your controller url"**
  - **export PINAKES_CONTROLLER_TOKEN="Your Token"**
  - **export PINAKES_CONTROLLER_VERIFY_SSL="False"**

```
./tools/minikube/scripts/start_pods.sh
```

To login to the UI use
https://catalog.k8s.local/api/pinakes/auth/login/

To access the keycloak server running inside the cluster use the following URL
http://keycloak.k8s.local/auth  (Default userid is admin password is admin)


To login to the catalog app using API endpoint
https://catalog.k8s.local/api/pinakes/auth/login/
When prompted enter the userid/password (barney.sample/barney)

To access the api DRF pages use

https://catalog.k8s.local/api/pinakes/v1/schema/openapi.json
https://catalog.k8s.local/api/pinakes/v1/portfolios/ (You wont be able to get to this link without logging in first)

### Applying local code changes for testing
To deploy your code changes that you have made locally before creating a PR you can redeploy the app using
```
./tools/minikube/scripts/redeploy_app.sh
```

This will stop the app, worker and scheduler pods, build the image with latest changes and
start the app, worker and scheduler pods.

### Starting a fresh with a clean env 
To delete all the pods and reset the application, run the helper_script delete_pods.sh.
The -d option deletes the persistent volumes so you can a fresh start

```
./tools/minikube/scripts/delete_pods.sh -d
```

## About credentials

When pinakes starts up it creates the required roles, policies, scopes, permissions (optionally groups and users) by using an ansible collection. The roles, policies, scopes and permissions are defined in the collection. The optional group and user data is stored in tools/keycloak_setup/dev.yml

For ease of development as part of the keycloak setup we create the following groups

 - **catalog-admin**
 - **catalog-user**
 - **approval-admin**
 - **approval-user**
 - **approval-approver**

The following groups are created

 - **Information Technology - Sample** (roles assigned catalog-admin, approval-admin)
 - **Marketing - Sample** (roles assigned catalog-user, approval-user)
 - **Finance - Sample** (roles assigned approval-approver)

The following users are also created

 - **fred.sample** (member of Information Technology - Sample) password: fred
 - **barney.sample** (member of Marketing - Sample) password: barney
 - **wilma.sample** (member of Finance - Sample) password: wilma

The default passwords can be changed by modifying the file **tools/keycloak_setup/dev.yml**
