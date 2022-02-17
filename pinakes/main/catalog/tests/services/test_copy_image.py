"""Test copy image service"""
import pytest

from pinakes.main.models import (
    Image,
)
from pinakes.main.catalog.tests.factories import (
    ImageFactory,
)
from pinakes.main.catalog.services.copy_image import (
    CopyImage,
)


@pytest.mark.django_db
def test_copy_image():
    image = ImageFactory()

    assert Image.objects.count() == 1

    svc = CopyImage(image)
    svc.process()

    assert Image.objects.count() == 2
    assert Image.objects.first().file.name != Image.objects.last().file.name

    new_image = svc.new_icon
    new_image.delete()
