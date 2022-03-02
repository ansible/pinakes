For Authentication and Authorization Pinakes uses [Keycloak](https://github.com/chambridge/galaxy_ng/tree/poc-keycloak-py-social). Keycloak can be configured to use a customers LDAP Server.


Pinakes runs on-prem alongside the [Automation Controller](https://www.ansible.com/products/controller) and communicates with it over REST APIs. The product is broken up into 3 main areas

 1. Catalog, deals with the creation of Products, Portfolios and Orders
 2. Approval, deals with the Approval process and notifications
 3. Inventory, deals with connecting to the Automation Controller using REST API to fetch objects and launch Automation Controller Jobs.

![Pinakes Architecture Diagram](./pinakes.png?raw=true)
