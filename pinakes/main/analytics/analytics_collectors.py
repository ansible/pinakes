import os

import platform
import distro
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from insights_analytics_collector import CsvFileSplitter, register

from pinakes.main.analytics.collector import AnalyticsCollector
from pinakes.main.analytics.package import Package
from pinakes.main.approval.models import Request
from pinakes.main.catalog import models
from pinakes.main.common.models import Group
from pinakes.main.inventory.models import ServiceInventory


@register(
    "config",
    "1.0",
    description=_("General platform configuration."),
    config=True,
)
def config(since, **kwargs):
    # TODO:
    # license_info = get_license()
    license_info = {}
    install_type = "traditional"
    if os.environ.get("container") == "oci":
        install_type = "openshift"
    elif "KUBERNETES_SERVICE_PORT" in os.environ:
        install_type = "k8s"
    return {
        "platform": {
            "system": platform.system(),
            "dist": distro.linux_distribution(),
            "release": platform.release(),
            "type": install_type,
        },
        # 'install_uuid': settings.INSTALL_UUID,
        # 'instance_uuid': settings.SYSTEM_UUID,
        # 'tower_url_base': settings.TOWER_URL_BASE,
        # 'tower_version': get_awx_version(),
        "tower_version": "1.0.0",
        "license_type": license_info.get("license_type", "UNLICENSED"),
        "free_instances": license_info.get("free_instances", 0),
        "total_licensed_instances": license_info.get("instance_count", 0),
        "license_expiry": license_info.get("time_remaining", 0),
        # 'pendo_tracking': settings.PENDO_TRACKING_STATE,
        # 'authentication_backends': settings.AUTHENTICATION_BACKENDS,
        # 'logging_aggregators': settings.LOG_AGGREGATOR_LOGGERS,
        # 'external_logger_enabled': settings.LOG_AGGREGATOR_ENABLED,
    }


@register(
    "sources_table",
    "1.0",
    format="csv",
    description=_("Data on sources"),
)
def sources_table(since, full_path, until, **kwargs):
    source_query = """COPY (SELECT main_source.id,
       main_source.name,
       main_source.created_at,
       main_source.updated_at,
       main_source.refresh_state,
       main_source.refresh_started_at,
       main_source.refresh_finished_at,
       main_source.last_checked_at,
       main_source.last_available_at,
       main_source.availability_status
       FROM main_source
       ORDER BY main_source.id ASC) TO STDOUT WITH CSV HEADER
    """

    return _simple_csv(full_path, "sources", source_query)


@register(
    "service_offerings_table",
    "1.0",
    format="csv",
    description=_("Data on service_offerings"),
)
def service_offerings_table(since, full_path, until, **kwargs):
    service_offering_query = """COPY (SELECT main_serviceoffering.id,
        main_serviceoffering.name,
        main_serviceoffering.created_at,
        main_serviceoffering.updated_at,
        main_serviceoffering.source_id,
        main_serviceoffering.source_ref,
        main_serviceoffering.service_inventory_id,
        main_serviceoffering.survey_enabled,
        main_serviceoffering.kind,
        main_serviceoffering.extra
        FROM main_serviceoffering
        WHERE ((main_serviceoffering.created_at > '{0}'
                AND main_serviceoffering.created_at <= '{1}')
                OR (main_serviceoffering.updated_at > '{0}'
                AND main_serviceoffering.updated_at <= '{1}'))
        ORDER BY main_serviceoffering.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "service_offerings", service_offering_query)


@register(
    "service_offering_nodes_table",
    "1.0",
    format="csv",
    description=_("Data on service_offering_nodes"),
)
def service_offering_nodes_table(since, full_path, until, **kwargs):
    service_offering_node_query = """COPY (SELECT main_serviceofferingnode.id,
        main_serviceofferingnode.created_at,
        main_serviceofferingnode.updated_at,
        main_serviceofferingnode.source_ref,
        main_serviceofferingnode.source_id,
        main_serviceofferingnode.service_inventory_id,
        main_serviceofferingnode.service_offering_id,
        main_serviceofferingnode.root_service_offering_id,
        main_serviceofferingnode.extra
        FROM main_serviceofferingnode
        WHERE ((main_serviceofferingnode.created_at > '{0}'
            AND main_serviceofferingnode.created_at <= '{1}')
            OR (main_serviceofferingnode.updated_at > '{0}'
            AND main_serviceofferingnode.updated_at <= '{1}'))
        ORDER BY main_serviceofferingnode.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(
        full_path, "service_offering_nodes", service_offering_node_query
    )


@register(
    "service_instances_table",
    "1.0",
    format="csv",
    description=_("Data on service_instances"),
)
def service_instances_table(since, full_path, until, **kwargs):
    service_instance_query = """COPY (SELECT main_serviceinstance.id,
        main_serviceinstance.created_at,
        main_serviceinstance.updated_at,
        main_serviceinstance.source_ref,
        main_serviceinstance.source_id,
        main_serviceinstance.service_plan_id,
        main_serviceinstance.service_offering_id,
        main_serviceinstance.service_inventory_id,
        main_serviceinstance.external_url,
        main_serviceinstance.extra
        FROM main_serviceinstance
        WHERE ((main_serviceinstance.created_at > '{0}'
            AND main_serviceinstance.created_at <= '{1}')
            OR (main_serviceinstance.updated_at > '{0}'
            AND main_serviceinstance.updated_at <= '{1}'))
        ORDER BY main_serviceinstance.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "service_instances", service_instance_query)


@register(
    "service_inventories_table",
    "1.0",
    format="csv",
    description=_("Data on service_inventories"),
)
def service_inventories_table(since, full_path, until, **kwargs):
    service_inventory_query = """COPY (SELECT main_serviceinventory.id,
        main_serviceinventory.created_at,
        main_serviceinventory.updated_at,
        main_serviceinventory.name,
        main_serviceinventory.source_ref,
        main_serviceinventory.source_id,
        main_serviceinventory.extra
        FROM main_serviceinventory
        WHERE ((main_serviceinventory.created_at > '{0}'
            AND main_serviceinventory.created_at <= '{1}')
            OR (main_serviceinventory.updated_at > '{0}'
            AND main_serviceinventory.updated_at <= '{1}'))
        ORDER BY main_serviceinventory.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(
        full_path, "service_inventories", service_inventory_query
    )


@register(
    "portfolios_table",
    "1.0",
    format="csv",
    description=_("Data on portfolios"),
)
def portfolios_table(since, full_path, until, **kwargs):
    portfolio_query = """COPY (SELECT main_portfolio.id,
        main_portfolio.created_at,
        main_portfolio.updated_at,
        main_portfolio.name,
        main_portfolio.user_id,
        main_portfolio.enabled,
        main_portfolio.share_count
        FROM main_portfolio
        WHERE ((main_portfolio.created_at > '{0}'
            AND main_portfolio.created_at <= '{1}')
            OR (main_portfolio.updated_at > '{0}'
            AND main_portfolio.updated_at <= '{1}'))
        ORDER BY main_portfolio.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "portfolios", portfolio_query)


@register(
    "portfolio_items_table",
    "1.0",
    format="csv",
    description=_("Data on portfolio_items"),
)
def portfolio_items_table(since, full_path, until, **kwargs):
    portfolio_item_query = """COPY (SELECT main_portfolioitem.id,
        main_portfolioitem.created_at,
        main_portfolioitem.updated_at,
        main_portfolioitem.name,
        main_portfolioitem.user_id,
        main_portfolioitem.portfolio_id,
        main_portfolioitem.favorite,
        main_portfolioitem.orphan,
        main_portfolioitem.state,
        main_portfolioitem.service_offering_ref,
        main_portfolioitem.service_offering_source_ref
        FROM main_portfolioitem
        WHERE ((main_portfolioitem.created_at > '{0}'
            AND main_portfolioitem.created_at <= '{1}')
            OR (main_portfolioitem.updated_at > '{0}'
            AND main_portfolioitem.updated_at <= '{1}'))
        ORDER BY main_portfolioitem.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "portfolio_items", portfolio_item_query)


@register(
    "orders_table",
    "1.0",
    format="csv",
    description=_("Data on orders"),
)
def orders_table(since, full_path, until, **kwargs):
    order_query = """COPY (SELECT main_order.id,
        main_order.created_at,
        main_order.updated_at,
        main_order.user_id,
        main_order.state,
        main_order.order_request_sent_at,
        main_order.completed_at
        FROM main_order
        WHERE ((main_order.created_at > '{0}'
            AND main_order.created_at <= '{1}')
            OR (main_order.updated_at > '{0}'
            AND main_order.updated_at <= '{1}'))
        ORDER BY main_order.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "orders", order_query)


@register(
    "order_items_table",
    "1.0",
    format="csv",
    description=_("Data on order_items"),
)
def order_items_table(since, full_path, until, **kwargs):
    order_item_query = """COPY (SELECT main_orderitem.id,
        main_orderitem.created_at,
        main_orderitem.updated_at,
        main_orderitem.order_id,
        main_orderitem.portfolio_item_id,
        main_orderitem.user_id,
        main_orderitem.inventory_task_ref,
        main_orderitem.inventory_service_plan_ref,
        main_orderitem.service_instance_ref,
        main_orderitem.name,
        main_orderitem.state,
        main_orderitem.order_request_sent_at,
        main_orderitem.completed_at,
        main_orderitem.count
        FROM main_orderitem
        WHERE ((main_orderitem.created_at > '{0}'
            AND main_orderitem.created_at <= '{1}')
            OR (main_orderitem.updated_at > '{0}'
            AND main_orderitem.updated_at <= '{1}'))
        ORDER BY main_orderitem.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "order_items", order_item_query)


@register(
    "approval_requests_table",
    "1.0",
    format="csv",
    description=_("Data on approval_requests"),
)
def approval_requests_table(since, full_path, until, **kwargs):
    approval_request_query = """COPY (SELECT main_approvalrequest.id,
        main_approvalrequest.created_at,
        main_approvalrequest.updated_at,
        main_approvalrequest.order_id,
        main_approvalrequest.approval_request_ref,
        main_approvalrequest.request_completed_at,
        main_approvalrequest.state
        FROM main_approvalrequest
        WHERE ((main_approvalrequest.created_at > '{0}'
            AND main_approvalrequest.created_at <= '{1}')
            OR (main_approvalrequest.updated_at > '{0}'
            AND main_approvalrequest.updated_at <= '{1}'))
        ORDER BY main_approvalrequest.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "approval_requests", approval_request_query)


@register(
    "service_plans_table",
    "1.0",
    format="csv",
    description=_("Data on service_plans"),
)
def service_plans_table(since, full_path, until, **kwargs):
    service_plan_query = """COPY (SELECT main_serviceplan.id,
        main_serviceplan.created_at,
        main_serviceplan.updated_at,
        main_serviceplan.name,
        main_serviceplan.portfolio_item_id,
        main_serviceplan.inventory_service_plan_ref,
        main_serviceplan.service_offering_ref,
        main_serviceplan.outdated
        FROM main_serviceplan
        WHERE ((main_serviceplan.created_at > '{0}'
            AND main_serviceplan.created_at <= '{1}')
            OR (main_serviceplan.updated_at > '{0}'
            AND main_serviceplan.updated_at <= '{1}'))
        ORDER BY main_serviceplan.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "service_plans", service_plan_query)


@register(
    "templates_table",
    "1.0",
    format="csv",
    description=_("Data on templates"),
)
def templates_table(since, full_path, until, **kwargs):
    template_query = """COPY (SELECT main_template.id,
        main_template.created_at,
        main_template.updated_at,
        main_template.title
        FROM main_template
        WHERE ((main_template.created_at > '{0}'
            AND main_template.created_at <= '{1}')
            OR (main_template.updated_at > '{0}'
            AND main_template.updated_at <= '{1}'))
        ORDER BY main_template.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "templates", template_query)


@register(
    "workflows_table",
    "1.0",
    format="csv",
    description=_("Data on workflows"),
)
def workflows_table(since, full_path, until, **kwargs):
    workflow_query = """COPY (SELECT main_workflow.id,
        main_workflow.created_at,
        main_workflow.updated_at,
        main_workflow.name,
        main_workflow.template_id,
        main_workflow.group_refs,
        main_workflow.internal_sequence
        FROM main_workflow
        WHERE ((main_workflow.created_at > '{0}'
            AND main_workflow.created_at <= '{1}')
            OR (main_workflow.updated_at > '{0}'
            AND main_workflow.updated_at <= '{1}'))
        ORDER BY main_workflow.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "workflows", workflow_query)


@register(
    "requests_table",
    "1.0",
    format="csv",
    description=_("Data on requests"),
)
def requests_table(since, full_path, until, **kwargs):
    request_query = """COPY (SELECT main_request.id,
        main_request.created_at,
        main_request.updated_at,
        main_request.name,
        main_request.workflow_id,
        main_request.parent_id,
        main_request.user_id,
        main_request.state,
        main_request.decision,
        main_request.group_name,
        main_request.group_ref,
        main_request.notified_at,
        main_request.finished_at,
        main_request.number_of_children,
        main_request.number_of_finished_children
        FROM main_request
        WHERE ((main_request.created_at > '{0}'
            AND main_request.created_at <= '{1}')
            OR (main_request.updated_at > '{0}'
            AND main_request.updated_at <= '{1}'))
        ORDER BY main_request.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "requests", request_query)


@register(
    "actions_table",
    "1.0",
    format="csv",
    description=_("Data on actions"),
)
def actions_table(since, full_path, until, **kwargs):
    action_query = """COPY (SELECT main_action.id,
        main_action.created_at,
        main_action.updated_at,
        main_action.request_id,
        main_action.user_id,
        main_action.operation
        FROM main_action
        WHERE ((main_action.created_at > '{0}'
            AND main_action.created_at <= '{1}')
            OR (main_action.updated_at > '{0}'
            AND main_action.updated_at <= '{1}'))
        ORDER BY main_action.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "actions", action_query)


@register(
    "tag_links_table",
    "1.0",
    format="csv",
    description=_("Data on tag_links"),
)
def tag_links_table(since, full_path, until, **kwargs):
    tag_link_query = """COPY (SELECT main_taglink.id,
        main_taglink.created_at,
        main_taglink.updated_at,
        main_taglink.workflow_id,
        main_taglink.app_name,
        main_taglink.tag_name,
        main_taglink.object_type
        FROM main_taglink
        WHERE ((main_taglink.created_at > '{0}'
            AND main_taglink.created_at <= '{1}')
            OR (main_taglink.updated_at > '{0}'
            AND main_taglink.updated_at <= '{1}'))
        ORDER BY main_taglink.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "tag_links", tag_link_query)


@register(
    "groups_table",
    "1.0",
    format="csv",
    description=_("Data on groups"),
)
def groups_table(since, full_path, until, **kwargs):
    group_query = """COPY (SELECT main_group.id,
        main_group.name,
        main_group.path,
        main_group.parent_id,
        main_group.last_sync_time
        FROM main_group
        WHERE (main_group.last_sync_time > '{0}'
            AND main_group.last_sync_time <= '{1}')
        ORDER BY main_group.id ASC) TO STDOUT WITH CSV HEADER
    """.format(
        since.isoformat(), until.isoformat()
    )

    return _simple_csv(full_path, "groups", group_query)


@register(
    "product_counts",
    "1.0",
    description=_("Counts of orders by products"),
)
def product_counts(since, **kwargs):
    counts = {}

    products = models.PortfolioItem.objects.values(
        "id",
        "name",
        "portfolio_id",
        "service_offering_ref",
        "service_offering_source_ref",
    )

    for product in products:
        order_item_list = []
        for item in models.OrderItem.objects.filter(
            portfolio_item_id=product["id"]
        ).values("id", "name", "state", "order_id", "inventory_task_ref"):
            order_item_list.append(item)

        if bool(order_item_list):
            counts[product["id"]] = {
                "name": product["name"],
                "portfolio_id": product["portfolio_id"],
                "service_offering_ref": product["service_offering_ref"],
                "service_offering_source_ref": product[
                    "service_offering_source_ref"
                ],
                "order items": order_item_list,
            }

    return counts


@register(
    "tag_counts_by_portfolio",
    "1.0",
    description=_("Counts of tags by portfolios"),
)
def tag_counts_by_portfolio(since, **kwargs):
    counts = {}

    portfolios = models.Portfolio.objects.all()

    for portfolio in portfolios:
        tag_resource_list = []
        for resource in portfolio.tag_resources:
            tag_resource_list.append(
                {
                    "id": resource.id,
                    "name": resource.name,
                    "slug": resource.slug,
                }
            )

        if bool(tag_resource_list):
            counts[portfolio.id] = {
                "name": portfolio.name,
                "tag_resources": {
                    "app_name": "catalog",
                    "object_type": "Portfolio",
                    "tags": tag_resource_list,
                },
            }

    return counts


@register(
    "tag_counts_by_product",
    "1.0",
    description=_("Counts of tags by products"),
)
def tag_counts_by_product(since, **kwargs):
    counts = {}

    products = models.PortfolioItem.objects.all()

    for product in products:
        tag_resource_list = []
        for resource in product.tag_resources:
            tag_resource_list.append(
                {
                    "id": resource.id,
                    "name": resource.name,
                    "slug": resource.slug,
                }
            )

        if bool(tag_resource_list):
            counts[product.id] = {
                "name": product.name,
                "tag_resources": {
                    "app_name": "catalog",
                    "object_type": "PortfolioItem",
                    "tags": tag_resource_list,
                },
            }

    return counts


@register(
    "tag_counts_by_service_intentory",
    "1.0",
    description=_("Counts of tags by service_intentories"),
)
def tag_counts_by_service_intentory(since, **kwargs):
    counts = {}

    service_intentories = ServiceInventory.objects.all()

    for service_intentory in service_intentories:
        tag_resource_list = []
        for resource in service_intentory.tags.all():
            tag_resource_list.append(
                {
                    "id": resource.id,
                    "name": resource.name,
                    "slug": resource.slug,
                }
            )

        if bool(tag_resource_list):
            counts[service_intentory.id] = {
                "name": service_intentory.name,
                "tag_resources": {
                    "app_name": "inventory",
                    "object_type": "ServiceInventory",
                    "tags": tag_resource_list,
                },
            }

    return counts


@register(
    "orders_data_by_product",
    "1.0",
    description=_("Order data by product"),
)
def orders_data_by_product(since, **kwargs):
    counts = {}

    products = models.PortfolioItem.objects.values(
        "id",
        "name",
        "created_at",
        "updated_at",
    )

    for product in products:
        order_items = models.OrderItem.objects.filter(
            portfolio_item_id=product["id"]
        ).values()

        order_list = []
        sum_time_spent_in_tower = 0.0
        num_orders = 0

        for item in order_items:
            order = models.Order.objects.filter(id=item["order_id"]).first()
            if order.completed_at and order.order_request_sent_at:
                sum_time_spent_in_tower += (
                    order.completed_at - order.order_request_sent_at
                ).total_seconds()
                num_orders += 1

            order_list.append(order)

        completed = [
            {
                "id": order.id,
                "state": order.state,
                "tenant_id": order.tenant_id,
                "user_id": order.user_id,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "order_sent_at": order.order_request_sent_at.isoformat()
                if order.order_request_sent_at
                else "",
                "completed_at": order.completed_at.isoformat(),
            }
            for order in order_list
            if order.state == models.Order.State.COMPLETED
        ]
        failed = [
            {
                "id": order.id,
                "state": order.state,
                "tenant_id": order.tenant_id,
                "user_id": order.user_id,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "order_sent_at": order.order_request_sent_at.isoformat()
                if order.order_request_sent_at
                else "",
                "completed_at": order.completed_at.isoformat(),
            }
            for order in order_list
            if order.state == models.Order.State.FAILED
        ]
        stuck = [
            {
                "id": order.id,
                "state": order.state,
                "tenant_id": order.tenant_id,
                "user_id": order.user_id,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "order_sent_at": order.order_request_sent_at.isoformat()
                if order.order_request_sent_at
                else "",
                "completed_at": order.completed_at.isoformat(),
            }
            for order in order_list
            if order.state == models.Order.State.PENDING
            or order.state == models.Order.State.CREATED
            or order.state == models.Order.State.ORDERED
        ]

        if bool(order_list):
            counts[product["id"]] = {
                "id": product["id"],
                "name": product["name"],
                "average_time_spent_in_tower": sum_time_spent_in_tower
                / num_orders,
                "completed_orders": completed,
                "failed_orders": failed,
                "stuck_orders": stuck,
            }

    return counts


@register(
    "approval_request_time_spent_by_group",
    "1.0",
    description=_("Approval request time spent by group"),
)
def approval_request_time_spent_by_groups(since, **kwargs):
    counts = {}

    groups = Group.objects.values(
        "id",
        "name",
    )
    for group in groups:
        request_list = []
        for request in Request.objects.filter(group_name=group["name"]).values(
            "id",
            "name",
            "created_at",
            "updated_at",
            "notified_at",
            "finished_at",
            "group_name",
        ):
            request_list.append(request)

        if bool(request_list):
            sum_time_spent = 0.0
            time_spent_intervals = {}

            for request in request_list:
                if request["finished_at"]:
                    time_spent_intervals[request["id"]] = (
                        request["finished_at"] - request["notified_at"]
                    )
                else:  # request is waiting for processing
                    time_spent_intervals[request["id"]] = (
                        now() - request["notified_at"]
                    )
                request["time_spent_in_approval"] = time_spent_intervals[
                    request["id"]
                ].total_seconds()

                sum_time_spent += time_spent_intervals[
                    request["id"]
                ].total_seconds()

            counts[group["name"]] = {
                "max_time_spent": max(
                    time_spent_intervals.values()
                ).total_seconds(),
                "min_time_spent": min(
                    time_spent_intervals.values()
                ).total_seconds(),
                "average_time_spent": sum_time_spent / len(request_list),
                "requests": [
                    {
                        "id": request["id"],
                        "name": request["name"],
                        "time_spent_in_approval": request[
                            "time_spent_in_approval"
                        ],
                        "created_at": request["created_at"].isoformat(),
                        "updated_at": request["updated_at"].isoformat(),
                        "notified_at": request["notified_at"].isoformat()
                        if request["notified_at"]
                        else "",
                        "finished_at": request["finished_at"].isoformat()
                        if request["finished_at"]
                        else "",
                    }
                    for request in request_list
                ],
            }

    return counts


def _simple_csv(
    full_path, file_name, query, max_data_size=Package.MAX_DATA_SIZE
):
    file_path = _get_file_path(full_path, file_name)
    file = CsvFileSplitter(filespec=file_path, max_file_size=max_data_size)

    with AnalyticsCollector.db_connection().cursor() as cursor:
        cursor.copy_expert(query, file)

    return file.file_list()


def _get_file_path(path, table):
    return os.path.join(path, table + "_table.csv")
