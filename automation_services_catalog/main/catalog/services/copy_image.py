"""Copy Image service"""
import logging
import os
import random
import string
from django.core.files.base import ContentFile

from automation_services_catalog.main.catalog.models import Image


logger = logging.getLogger("catalog")


class CopyImage:
    """Copy image service"""

    def __init__(self, image):
        self.icon = image
        self.new_icon = None

    def process(self):
        existing_image_names = [
            image.file.name for image in Image.objects.all()
        ]
        names = os.path.splitext(self.icon.file.name)

        while True:
            rad_sfx = "".join(
                random.choices(string.ascii_letters + string.digits, k=6)
            )
            new_name = "{}{}{}".format(names[0], rad_sfx, names[-1])
            if new_name not in existing_image_names:
                break

        with open(self.icon.file.path, "rb") as icon:
            data = icon.read()

        self.new_icon = Image()
        self.new_icon.file.save(new_name, ContentFile(data))
        self.new_icon.source_ref = self.icon.source_ref
        self.new_icon.save()

        return self
