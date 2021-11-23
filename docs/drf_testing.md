## Testing API end points to launch a Tower Job

While we wait for the UI we can do some basic testing by calling the REST API end points directly.

1. Login to keycloak
     [http://catalog.k8s.local/login/keycloak-oidc/](http://catalog.k8s.local/login/keycloak-oidc/)
     Login as user: barney password: barney
     if the login is successful you would get a Page not found 404 on http://catalog.k8s.local/accounts/profile/
![Alt_LoginSuccess](./drf_images/successful_login.png?raw=true)
2. Start a Inventory Refresh
     [http://catalog.k8s.local/api/ansible-catalog/v1/sources/1/refresh/](http://catalog.k8s.local/api/ansible-catalog/v1/sources/1/refresh/)
    Please note the Source id is always 1 when running these tests since there is only 1 source.
     Hit the PATCH button and 
3. Check if service offerings were imported from Controller
[http://catalog.k8s.local/api/ansible-catalog/v1/service_offerings/](http://catalog.k8s.local/api/ansible-catalog/v1/service_offerings/)
![Alt_ServiceOfferings](./drf_images/service_offerings.png?raw=true)
4. Note the id of a service offering that we can add to the portfolio
5. Get the Service Plan associated with the Service Offering, in he example the service offering id chosen is 2.
[http://catalog.k8s.local/api/ansible-catalog/v1/service_offerings/2/service_plans/](http://catalog.k8s.local/api/ansible-catalog/v1/service_offerings/2/service_plans/)
![Alt_ServicePlans](./drf_images/service_plan.png?raw=true)
6. Note the fields we would need to populate
 In the example
    * username
    * quest
    * airspeed
    * int_value
   We would need this when ordering
7. Create a Portfolio
![Alt_CreatePortfolio](./drf_images/create_portfolio.png?raw=true)
8. Create a Portfolio Item
   Service Offering Ref is 2
   Give it a name and description and hit the Post Button
![Alt_CreatePortfolioItem](./drf_images/create_portfolio_item.png?raw=true)
 
10. Create a new order
     [http://catalog.k8s.local/api/ansible-catalog/v1/orders/](http://catalog.k8s.local/api/ansible-catalog/v1/orders/)
![Alt_OrderCreated](./drf_images/order_created.png?raw=true)
     Hit the Post Buttom, note the order is that will be needed in following steps. In this example it is 6
11. Add an order item to the order
       [http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/order_items/](http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/order_items/) 
       Set the Service Parameters based on the fields we collected
       
    ```
    {
    "username": "fred",
    "quest": "Test Catalog",
    "airspeed": 5.0,
    "int_value": 9
    }
    ```
    Set the Portfolio Item
    Hit the POST button to create the new order item. 
![Alt_AddOrderItem](./drf_images/add_an_order_item.png?raw=true)
12. Submit the order
[**http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/submit/**](http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/submit/) 
Hit the Post button 
13. Check the Order Progress
[**http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/progress_messages/**](http://catalog.k8s.local/api/ansible-catalog/v1/orders/6/progress_messages/)
![Alt_ProgressMessages](./drf_images/progress_messages.png?raw=true)

