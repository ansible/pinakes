## About credentials

When pinakes starts up it creates the required roles, policies, scopes, permissions (optionally groups and users) by using an ansible collection. The roles, policies, scopes and permissions are defined in the collection. The optional group and user data is stored in tools/keycloak_setup/dev.yml

For ease of development as part of the keycloak setup we create the following groups

 - **catalog-admin**
 - **catalog-user**
 - **approval-admin**
 - **approval-approver**

The following groups are created

 - **Information Technology - Sample** (roles assigned catalog-admin, approval-admin)
 - **Marketing - Sample** (roles assigned catalog-user)
 - **Finance - Sample** (roles assigned approval-approver)

The following users are also created

 - **fred.sample** (member of Information Technology - Sample) password: fred
 - **barney.sample** (member of Marketing - Sample) password: barney
 - **wilma.sample** (member of Finance - Sample) password: wilma

The default passwords can be changed by modifying the file **tools/keycloak_setup/dev.yml**
