## Using minikube for development
###  Setup minikube
[Install minikube](https://minikube.sigs.k8s.io/docs/start/)
Start minikube
(for macOS use hyperkit driver ONLY "minikube start --driver=hyperkit")


Since the pinakes, keycloak, postgres, redis all run inside the minikube cluster we need to expose the pinakes and keycloak services from the cluster to your local dev machine using ingress. We need to enable ingress on the minikube cluster

```
minikube addons enable ingress
```

[More on that here](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)

Get the IP address of the minikube cluster
```
minikube ip
```

The ingress uses 2 hard coded hosts **pinakes** and **keycloak** to route the traffic to the appropriate services so we need to add the the IP address from the above command into /etc/hosts. The /etc/hosts should have this line
```
<<ip_from_minikube_ip>> pinakes.k8s.local keycloak.k8s.local
```

### Clone this repository
```
  git clone https://github.com/ansible/pinakes
  cd pinakes
```

### Building the image

If you have docker installed on your device it might help to set minikube as the docker daemon using the following command before doing the build
```
eval $(minikube -p minikube docker-env)
```

Build the image

```
minikube image build -t localhost/pinakes -f tools/docker/Dockerfile .
```
### Starting the app
Once this has been setup you can start the deployments, services and ingress service in the directory tools/minikube/templates. A helper script creates a Kubernetes namespace called **catalog** and runs all the deployments in that namespace. The helper scripts requires 3 environment variables to locate the Automation Controller.
  - **export PINAKES_CONTROLLER_URL="Your controller URL"**
  - **export PINAKES_CONTROLLER_TOKEN="Your Token"**
  - **export PINAKES_CONTROLLER_VERIFY_SSL="False"**

```
./tools/minikube/scripts/start_pods.sh
```

### Login to PINAKES
 * https://pinakes.k8s.local/api/pinakes/auth/login/
 * [Credentials](./CREDENTIALS.md)

### Keycloak
To access Keycloak admin page use https://keycloak.k8s.local/auth (admin/admin)

To access the api DRF pages use

https://pinakes.k8s.local/api/pinakes/v1/schema/openapi.json
https://pinakes.k8s.local/api/pinakes/v1/portfolios/ (You wont be able to get to this link without logging in first)

### Applying local code changes for testing
To deploy your code changes that you have made locally before creating a PR you can re-deploy the app using
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
