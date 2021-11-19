#
# Create a Source object if one doesn't exist
from ansible_catalog.main.models import Source, Tenant

if Source.objects.count() == 0:
    Source.objects.create(name="source_1", tenant=Tenant.current())
