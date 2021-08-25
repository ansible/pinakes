from django.db.models.signals import pre_save
from django.dispatch import receiver

from main.catalog.models import OrderItem
from main.catalog.services.sanitize_parameters import SanitizeParameters


@receiver(pre_save, sender=OrderItem)
def sanitize_parameters(sender, instance, **kwargs):
    if instance.id is not None:
        sanitized_parameters = (
            SanitizeParameters(instance).process().sanitized_parameters
        )
        if instance.service_parameters == sanitized_parameters:
            return

        instance.service_parameters_raw = instance.service_parameters
        instance.service_parameters = sanitized_parameters
