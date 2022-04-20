## Using docker-compose for development

### Requirements

You will need to install docker/podman and docker-compose.

You must first initialize the api socket for podman:

```
# only Linux
systemctl --user enable --now podman.socket
```

And then export the socket:

```
# only linux
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock
```

### Clone this repository

```
 git clone https://github.com/ansible/pinakes
 cd pinakes
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

Once it has finished you can try to open <https://localhost:8443/api/pinakes/v1/>
You can do log in with <https://localhost:8443/login/keycloak/>

* [Credentials](./CREDENTIALS.md)

You can open the UI with <https://localhost:8443/ui/catalog/index.html>
The project path is mounted in the pod and you can edit it in real time from outside the container.

You can get an interactive shell inside the application pod with the command:

```
docker-compose exec app bash
```

Remove the deployment (add `-v` flag to remove the volumes as well)

```
docker-compose down
```

### Deploy catalog in a production-like setup

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

## External access

By default, docker-compose is ready to work on localhost. If you want to make it accesible through the external IP address you have to override the `PINAKES_KEYCLOAK_REALM_FRONTEND_URL` variable in your `.env` file:

```
PINAKES_KEYCLOAK_REALM_FRONTEND_URL=https://[your-external-ip-address]:9443/auth
```

### Download the open api schema

<http://localhost:8000/api/pinakes/v1/schema/openapi.json>

### Try with swagger UI

<http://localhost:8000/api/pinakes/v1/schema/swagger-ui/>

## Overriding UI

You can override the UI's build providing your custom `catalog-ui.tar.gz` file inside `tools/docker/frontend/overrides` folder.
