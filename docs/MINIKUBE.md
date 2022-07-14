## Using minikube for development

###  Setup minikube

[Install minikube](https://minikube.sigs.k8s.io/docs/start/)
Start minikube (for macOS use hyperkit driver ONLY "minikube start --driver=hyperkit")


Since the pinakes, keycloak, postgres, redis all run inside the minikube cluster we need to expose
the pinakes and keycloak services from the cluster to your local dev machine using ingress.
We need to enable ingress on the minikube cluster
```
minikube addons enable ingress
```

[More on that here](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)

Get the IP address of the minikube cluster
```
minikube ip
```

The ingress uses 2 hard coded hosts **pinakes** and **keycloak** to route the traffic
to the appropriate services, so we need to add the IP address from the above command
into `/etc/hosts`. The `/etc/hosts` should have this line
```
<<ip_from_minikube_ip>> pinakes.k8s.local keycloak.k8s.local
```

### Clone this repository

```
  git clone https://github.com/ansible/pinakes
  cd pinakes
```

### Starting the app

Once minikube has been setup you can start the deployments, services and ingress service
in the directory `tools/minikube/templates`. A helper script creates a Kubernetes namespace
called **catalog** and runs all the deployments in that namespace.

The helper scripts requires 3 environment variables to locate the Automation Controller.
You can set this in a file called `minikube_env_vars`.
A sample file is located in `./tools/minikube/env_var.sample`. Copy this file to the root directory:
```
cp ./tools/minikube/env_vars.sample minikube_env_vars
```

Edit this file and set the 3 fields

  * `PINAKES_CONTROLLER_URL`
  * `PINAKES_CONTROLLER_TOKEN`
  * `PINAKES_CONTROLLER_VERIFY_SSL`

The `start_pods.sh` script will check and build the pinakes app image if it's missing.
```
./tools/minikube/scripts/start_pods.sh
```

### Set database encryption key

See [database encryption](./SECURITY.md#encryption).

### Login to PINAKES

 * https://pinakes.k8s.local/api/pinakes/auth/login/
 * [Credentials](./CREDENTIALS.md)

### Keycloak

To access Keycloak admin page use https://keycloak.k8s.local/auth
(username: `admin`, password: `admin`).

To access the api DRF pages use

* https://pinakes.k8s.local/api/pinakes/v1/schema/openapi.json
* https://pinakes.k8s.local/api/pinakes/v1/portfolios/ \
  (You won't be able to get to this link without logging in first)

### Applying local code changes for testing

To deploy your code changes that you have made locally
before creating a PR you can re-deploy the app using
```
./tools/minikube/scripts/redeploy_app.sh
```

This will stop the app, worker and scheduler pods, build the image with latest changes and
start the app, worker and scheduler pods.

### Starting a fresh with a clean env
To delete all the pods and reset the application, run the helper script delete_pods.sh.
The -d option deletes the persistent volumes so you can have a fresh start

```
./tools/minikube/scripts/delete_pods.sh -d
```

If you are on Mac deleting the pods might not clear out the databases you might have to do this
```
minikube ssh
sudo rm -rf /tmp/hostpath-provisioner/catalog/
```
### Optionally overriding UI and images

To override the UI tar file you can create a file in the following location
   * ./overrides/ui/catalog-ui.tar.gz

To override images and css you can store them in the following directories.
  * ./overrides/pinakes
  * ./overrides/approval
  * ./overrides/keycloak


### Cleanup & Miscellaneous

There might be times when you run out of disk space on the minikube vm.
To reclaim some of the space you can run the following command
```
minikube ssh
docker system prune  (when prompted enter y to continue)
exit
```

The `start_pods.sh` script builds the pinakes image if one doesn't exist.
If you want to rerun `start_pods.sh` it won't rebuild the image.
If you want `start_pods.sh` to rebuild the image you might want to delete it
before running `start_pods.sh`:
```
minikube image rm localhost/pinakes
```
