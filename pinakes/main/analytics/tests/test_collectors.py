""" Tests for metrics collection """
import csv
from datetime import timedelta
import os
import re
import shutil
import tempfile

from django.db.backends.sqlite3.base import SQLiteCursorWrapper
from django.utils.timezone import now

from pinakes.main.models import Source
from pinakes.main.approval.models import (
    TagLink,
    Template,
)
from pinakes.main.catalog.models import (
    ApprovalRequest,
    Portfolio,
    PortfolioItem,
)
from pinakes.main.approval.tests.factories import (
    ActionFactory,
    RequestFactory,
    WorkflowFactory,
)
from pinakes.main.catalog.tests.factories import (
    ApprovalRequestFactory,
    OrderFactory,
    OrderItemFactory,
    PortfolioFactory,
    PortfolioItemFactory,
    ServicePlanFactory,
)
from pinakes.main.common.tests.factories import GroupFactory
from pinakes.main.inventory.tests.factories import (
    ServiceInstanceFactory,
    ServiceInventoryFactory,
    ServiceOfferingFactory,
    ServiceOfferingNodeFactory,
)
from pinakes.main.analytics import analytics_collectors as collectors

import pytest


@pytest.fixture
def sqlite_copy_expert(request):
    # copy_expert is postgres-specific, and SQLite doesn't support it; mock its
    # behavior to test that it writes a file that contains stdout from events
    path = tempfile.mkdtemp(prefix="copied_tables")

    def write_stdout(self, sql, fd):
        # Would be cool if we instead properly disected the SQL query and verified
        # it that way. But instead, we just take the naive approach here.
        sql = sql.strip()
        assert sql.startswith("COPY (")
        assert sql.endswith(") TO STDOUT WITH CSV HEADER")

        sql = sql.replace("COPY (", "")
        sql = sql.replace(") TO STDOUT WITH CSV HEADER", "")
        # sqlite equivalent
        sql = sql.replace("ARRAY_AGG", "GROUP_CONCAT")
        # SQLite doesn't support isoformatted dates, because that would be useful
        sql = sql.replace("+00:00", "")
        i = re.compile(r"(?P<date>\d\d\d\d-\d\d-\d\d)T")
        sql = i.sub(r"\g<date> ", sql)

        # Remove JSON style queries
        # TODO: could replace JSON style queries with sqlite kind of equivalents
        sql_new = []
        for line in sql.split("\n"):
            if line.find("main_jobevent.event_data::") == -1:
                sql_new.append(line)
            elif not line.endswith(","):
                sql_new[-1] = sql_new[-1].rstrip(",")
        sql = "\n".join(sql_new)

        self.execute(sql)
        results = self.fetchall()
        headers = [i[0] for i in self.description]

        csv_handle = csv.writer(
            fd,
            delimiter=",",
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
            lineterminator="\n",
        )
        csv_handle.writerow(headers)
        csv_handle.writerows(results)

    setattr(SQLiteCursorWrapper, "copy_expert", write_stdout)
    request.addfinalizer(lambda: shutil.rmtree(path))
    request.addfinalizer(lambda: delattr(SQLiteCursorWrapper, "copy_expert"))
    return path


@pytest.mark.django_db
def test_source_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.sources_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "sources_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "name",
                "created_at",
                "updated_at",
                "refresh_state",
                "refresh_started_at",
                "refresh_finished_at",
                "last_checked_at",
                "last_available_at",
                "availability_status",
            ]
            assert len(lines) == 1
            assert lines[0][0] == "1"  # id
            assert lines[0][1] == "Automation Controller"  # name


@pytest.mark.django_db
def test_service_offering_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    service_offering = ServiceOfferingFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.service_offerings_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "service_offerings_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "name",
                "created_at",
                "updated_at",
                "source_id",
                "source_ref",
                "service_inventory_id",
                "survey_enabled",
                "kind",
                "extra",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(service_offering.id)
            assert lines[0][1] == service_offering.name


@pytest.mark.django_db
def test_service_offering_node_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    service_offering_node = ServiceOfferingNodeFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.service_offering_nodes_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(
            os.path.join(tmpdir, "service_offering_nodes_table.csv")
        ) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "source_ref",
                "source_id",
                "service_inventory_id",
                "service_offering_id",
                "root_service_offering_id",
                "extra",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(service_offering_node.id)


@pytest.mark.django_db
def test_service_instance_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    service_instance = ServiceInstanceFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.service_instances_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "service_instances_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "source_ref",
                "source_id",
                "service_plan_id",
                "service_offering_id",
                "service_inventory_id",
                "external_url",
                "extra",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(service_instance.id)


@pytest.mark.django_db
def test_service_inventories_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    service_inventory = ServiceInventoryFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.service_inventories_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "service_inventories_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "source_ref",
                "source_id",
                "extra",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(service_inventory.id)
            assert lines[0][3] == service_inventory.name


@pytest.mark.django_db
def test_portfolio_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    portfolio = PortfolioFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.portfolios_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "portfolios_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "user_id",
                "enabled",
                "share_count",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(portfolio.id)
            assert lines[0][3] == portfolio.name


@pytest.mark.django_db
def test_portfolio_item_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    portfolio_item = PortfolioItemFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.portfolio_items_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "portfolio_items_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "user_id",
                "portfolio_id",
                "favorite",
                "orphan",
                "state",
                "service_offering_ref",
                "service_offering_source_ref",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(portfolio_item.id)
            assert lines[0][3] == portfolio_item.name


@pytest.mark.django_db
def test_order_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    order = OrderFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.orders_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "orders_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "user_id",
                "state",
                "order_request_sent_at",
                "completed_at",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(order.id)
            assert lines[0][3] == str(order.user.id)


@pytest.mark.django_db
def test_order_item_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    order_item = OrderItemFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.order_items_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "order_items_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "order_id",
                "portfolio_item_id",
                "user_id",
                "inventory_task_ref",
                "inventory_service_plan_ref",
                "service_instance_ref",
                "name",
                "state",
                "order_request_sent_at",
                "completed_at",
                "count",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(order_item.id)
            assert lines[0][3] == str(order_item.order.id)
            assert lines[0][4] == str(order_item.portfolio_item.id)


@pytest.mark.django_db
def test_approval_request_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    approval_request = ApprovalRequestFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.approval_requests_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "approval_requests_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "order_id",
                "approval_request_ref",
                "request_completed_at",
                "state",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(approval_request.id)
            assert lines[0][3] == str(approval_request.order.id)


@pytest.mark.django_db
def test_service_plan_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    service_plan = ServicePlanFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.service_plans_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "service_plans_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "portfolio_item_id",
                "inventory_service_plan_ref",
                "service_offering_ref",
                "outdated",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(service_plan.id)
            assert lines[0][3] == service_plan.name


@pytest.mark.django_db
def test_template_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    template = Template.objects.first()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.templates_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "templates_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "title",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(template.id)
            assert lines[0][3] == template.title


@pytest.mark.django_db
def test_workflow_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    workflow = WorkflowFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.workflows_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "workflows_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "template_id",
                "group_refs",
                "internal_sequence",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(workflow.id)
            assert lines[0][3] == workflow.name


@pytest.mark.django_db
def test_request_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    request = RequestFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.requests_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "requests_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "name",
                "workflow_id",
                "parent_id",
                "user_id",
                "state",
                "decision",
                "group_name",
                "group_ref",
                "notified_at",
                "finished_at",
                "number_of_children",
                "number_of_finished_children",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(request.id)
            assert lines[0][3] == request.name


@pytest.mark.django_db
def test_action_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    action = ActionFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.actions_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "actions_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "request_id",
                "user_id",
                "operation",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(action.id)
            assert lines[0][3] == str(action.request.id)


@pytest.mark.django_db
def test_tag_link_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    workflow = WorkflowFactory()
    tag_link = TagLink.objects.create(
        app_name="catalog",
        object_type="Portfolio",
        tag_name="/abc",
        workflow=workflow,
        tenant=workflow.tenant,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.tag_links_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "tag_links_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "created_at",
                "updated_at",
                "workflow_id",
                "app_name",
                "tag_name",
                "object_type",
            ]
            assert len(lines) == 1
            assert lines[0][0] == str(tag_link.id)
            assert lines[0][3] == str(workflow.id)
            assert lines[0][4] == tag_link.app_name
            assert lines[0][5] == tag_link.tag_name
            assert lines[0][6] == tag_link.object_type


@pytest.mark.django_db
def test_group_table_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)
    group = GroupFactory()

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.groups_table(
            time_start, tmpdir, until=now() + timedelta(seconds=1)
        )
        with open(os.path.join(tmpdir, "groups_table.csv")) as f:
            reader = csv.reader(f)

            header = next(reader)
            lines = [line for line in reader]

            assert header == [
                "id",
                "name",
                "path",
                "parent_id",
                "last_sync_time",
            ]
            assert len(lines) == 1
            assert lines[0][0] == group.id
            assert lines[0][1] == group.name


@pytest.mark.django_db
def test_product_count_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)

    PortfolioItemFactory()  # no order on this product, should not count
    portfolio_item = PortfolioItemFactory()  # two orders on this product
    order = OrderFactory()
    OrderItemFactory(order=order, portfolio_item=portfolio_item)
    OrderItemFactory(order=OrderFactory(), portfolio_item=portfolio_item)

    results = collectors.product_counts(
        time_start, until=now() + timedelta(seconds=1)
    )

    assert results is not None
    assert [*results[portfolio_item.id].keys()] == [
        "name",
        "portfolio_id",
        "service_offering_ref",
        "service_offering_source_ref",
        "order items",
    ]
    assert len(results[portfolio_item.id]["order items"]) == 2
    assert [*results[portfolio_item.id]["order items"][0].keys()] == [
        "id",
        "name",
        "state",
        "order_id",
        "inventory_task_ref",
    ]


@pytest.mark.django_db
def test_tag_count_by_portfolio_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)

    portfolio = PortfolioFactory()
    portfolio.tags.add("/abc")

    results = collectors.tag_counts_by_portfolio(
        time_start, until=now() + timedelta(seconds=1)
    )

    assert len(results) == 1
    assert [*results[portfolio.id].keys()] == ["name", "tag_resources"]
    assert [*results[portfolio.id]["tag_resources"].keys()] == [
        "app_name",
        "object_type",
        "tags",
    ]
    assert len(results[portfolio.id]["tag_resources"]["tags"]) == 1
    assert results[portfolio.id]["tag_resources"]["tags"][0]["name"] == "/abc"


@pytest.mark.django_db
def test_tag_count_by_product_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)

    product = PortfolioItemFactory()
    product.tags.add("/abc")

    results = collectors.tag_counts_by_product(
        time_start, until=now() + timedelta(seconds=1)
    )

    assert len(results) == 1
    assert [*results[product.id].keys()] == ["name", "tag_resources"]
    assert [*results[product.id]["tag_resources"].keys()] == [
        "app_name",
        "object_type",
        "tags",
    ]
    assert len(results[product.id]["tag_resources"]["tags"]) == 1
    assert results[product.id]["tag_resources"]["tags"][0]["name"] == "/abc"


@pytest.mark.django_db
def test_tag_count_by_service_inventory_collector(sqlite_copy_expert):
    time_start = now() - timedelta(hours=9)

    service_inventory = ServiceInventoryFactory()
    service_inventory.tags.add("/abc")

    results = collectors.tag_counts_by_service_intentory(
        time_start, until=now() + timedelta(seconds=1)
    )

    assert len(results) == 1
    assert [*results[service_inventory.id].keys()] == ["name", "tag_resources"]
    assert [*results[service_inventory.id]["tag_resources"].keys()] == [
        "app_name",
        "object_type",
        "tags",
    ]
    assert len(results[service_inventory.id]["tag_resources"]["tags"]) == 1
    assert (
        results[service_inventory.id]["tag_resources"]["tags"][0]["name"]
        == "/abc"
    )
