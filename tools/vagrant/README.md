# Vagrant Dev Environment

We can run our dev environment in VirtualBox using Vagrant. We have 3 VMs running RHEL8

 1. NGINX (catalog.vm.local)
 2. Keycloak (keycloak.vm.local)
 3. Catalog VM (with Postgres, Redis, Catalog App, Catalog Worker, Catalog Scheduler)
 

# Pre requisites
* [Install Vagrant](https://www.vagrantup.com/downloads)
* You need the Red Hat Network (RHN) userid/password to access the RPM's for the different packages we need (Postgres, Redis,....)

## Installation
* git clone this repo
* We use the private network with the following 3 IP addresses for the VMs
	* 192.168.33.20 
	* 192.168.33.21
	* 192.168.33.22
  Please ensure that these IP addresses don't have conflicts in your environment. If they do choose 3 different addresses.
* Modify the tools/vagrant/data/env_vars file for the following
    * RHN Credentials 
	    * RHN_USER
	    * RHN_PASSWORD
    * Automation Controller information
	    * ANSIBLE_CATALOG_CONTROLLER_URL
	    * ANSIBLE_CATALOG_CONTROLLER_TOKEN
	    * ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL
    * Modify the **/etc/hosts** file to have the following lines
	    *  192.168.33.22 catalog.vm.local
	    * 192.168.33.20 keycloak.vm.local
* Change directory to ./tools/vagrant
* vagrant up
* Login to the browser using the following url https://catalog.vm.local

## Cleanup/Restart
Use **vagrant destroy** to cleanup the VM's 
 
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
* Currently the NGINX VM has some SELinux policy configured for dev environment which would have to be changed when used in production
