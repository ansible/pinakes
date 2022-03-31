
# Vagrant Dev Environment

We can run our dev environment in Virtual Box using Vagrant. We have 2 VMs running RHEL8

 1. Keycloak (keycloak.vm.local)
 2. Pinakes VM (with Postgres, Redis, NGINX, Catalog App, Catalog Worker, Catalog Scheduler)
 

# Pre requisites
* [Install Vagrant](https://www.vagrantup.com/downloads)
* You need the Red Hat Network (RHN) userid/password to access the RPM's for the different packages we need (Postgres, Redis,....)

## Installation
* Clone this repository
```
 git clone https://github.com/ansible/pinakes
 cd pinakes
```
* We use the private network with the following 2 IP addresses for the VMs
	* 192.168.33.20 
	* 192.168.33.21
	
  Please ensure that these IP addresses don't have conflicts in your environment. If they do choose 2 different addresses.
* Copy the tools/vagrant/data/env_vars.sample to tools/vagrant/data/env_vars 
* Modify the tools/vagrant/data/env_vars file for the following
    * RHN Credentials 
	    * RHN_USER
	    * RHN_PASSWORD
    * Automation Controller information
	    * PINAKES_CONTROLLER_URL
	    * PINAKES_CONTROLLER_TOKEN
	    * PINAKES_CONTROLLER_VERIFY_SSL
    * Modify the **/etc/hosts** file to have the following lines
	    *  192.168.33.21 pinakes.vm.local
	    * 192.168.33.20 keycloak.vm.local
* Change directory to ./tools/vagrant
* vagrant up
* Login to the browser using the following URL https://pinakes.vm.local The server uses self signed certificates.

## Cleanup/Restart
Use **vagrant destroy** to cleanup the VMs 
 
## Services
During the setup process we create a user called "catalog" and it runs 3 services
1. **catalog**
2. **catalog_scheduler**
3. **catalog_worker**

To look at the logs use

journalctl -u catalog > /tmp/catalog.log
journalctl -u catalog_worker > /tmp/catalog_worker.log
journalctl -u catalog_scheduler > /tmp/catalog_scheduler.log

## SELinux issues
* Files served by NGINX are in /var/lib/catalog/public
* Since NGNIX talks to the catalog app we need to use
    * setsebool -P httpd_can_network_connect on

## Login to PINAKES
 * https://pinakes.vm.local/api/pinakes/auth/login/
 * [Credentials](./CREDENTIALS.md)
## Keycloak
To access Keycloak admin page use http://keycloak.vm.local:8080/auth (admin/admin)
