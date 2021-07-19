
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
   You can override the Database and Tower information in your local development settings file.
   This settings file should not be checked into github, local settings file name should have a prefix of  **local** e.g.   **ansible_catalog/settings/local_info.py**
   
   To store tower info use the following keys
   
  * TOWER_TOKEN="Your Token"
  * TOWER_URL="Your Tower URL"
  * TOWER_VERIFY_SSL="False"
  
* Start the Server using development settings
      ```DJANGO_SETTINGS_MODULE=ansible_catalog.settings.development python3 manage.py runserver```
      
      Open your browser and open http://127.0.0.1:8000/catalog/api/v1/portfolios/
      
      When prompted provide the userid/password from the createsuperuser step

* After you have tested in the dev environment you can deactivate the virtual env by using
```deactivate```
