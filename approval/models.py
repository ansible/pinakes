from django.db import models
from django.db.models.functions import Length

from .basemodel import BaseModel

models.CharField.register_lookup(Length)


class Template(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_title_empty",
                check=models.Q(title__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_title_unique",
                fields=["title", "tenant"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Workflow(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    template = models.ForeignKey(Template, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=["name", "tenant", "template"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
