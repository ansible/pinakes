

# RBAC

Automation Services Catalog uses Keycloak for Authentication and Authorization. During the setup process we create the following roles along with other supporting objects. 

 - catalog-admin
 - catalog-user
 - approval-admin
 - approval-approver

## catalog-admin
Allows the logged in user to function as an Administrator and create, update, read, delete all objects in the Automation Services Catalog. A catalog-admin role doesn't allow you to Approve any pending requests. You would need the approval-admin role attached to the user to do that.

## catalog-user
Allows the logged in user to function as a regular user who can order the Products shared in Portfolios by the Catalog Administrator. It allows them to track the progress of their orders.

## approval-admin
Allows the logged in user to create, read, update, delete Approval Processes. Approve/Deny any pending requests.

## approval-approver
Allows the logged in user to Approve/Deny any pending requests. A approver cannot create Approval Processes.


## Applying RBAC
 - Create Groups in Keycloak and assign them one or more of the above mentioned roles.
 - Create Users in Keycloak and assign them a group membership to one of the created groups.

## A  sample admin group with catalog-admin and approval-admin roles
![Alt_AdminGroup](./admin-group.png?raw=true)

## A approver group with only the approval-approver role
![Alt_ApproverGroup](./approver-group.png?raw=true)

## A standard user group with the catalog-user role
![Alt_UserGroup](./regular-user-group.png?raw=true)

## Adding users to groups
![Alt_AddUserGroup](./adding-users-to-groups.png?raw=true)
