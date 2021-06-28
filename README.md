# Ansible Catalog

Ansible Catalog allows customers to expose their Ansible Job Templates and Workflows to business users with an added layer of governance. The Job Templates and Workflows are wrapped as Product into Portfolios which can be shared with different business users. An approval workflow can be attached to the Product or the Portfolio which will add the governance and notify the appropriate Administrators via email. Upon approval the Job Template or workflow will be launched on the Ansible Controller. Ansible Catalog also supports editing of Survey Specs to create different flavors of the Job Template or Workflow with pre-canned parameters so businesss users don't have to be concerned about the details of a parameter.

For Authentication and Authorization Ansible Catalog uses the Keycloak. Keycloak can be configured to use a customers LDAP Server.


Ansible Catalog runs on-prem along side the Ansible Controller and communicates with it over REST API's. The product is broken into 3 main areas

 1. Catalog, deals with the creation of Products, Portfolios and Orders
 2. Approval, deals with the Approval process and notification
 3. Inventory, deals with connecting to the Ansible Controller using REST API to fetch objects and launch Ansible Controller Jobs.

![Alt UsingUploadService](./docs/ansible_catalog.png?raw=true)
