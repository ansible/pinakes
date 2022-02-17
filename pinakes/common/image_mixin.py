from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from pinakes.main.catalog.serializers import (
    ImageSerializer,
)


class ImageMixin:
    """
    Image mixin shared with Catalog Portfolio and PortfolioItem
    """

    @extend_schema(
        request={"multipart/form-data": ImageSerializer},
        methods=("POST",),
        description="Create an icon",
    )
    @extend_schema(
        request={"multipart/form-data": ImageSerializer},
        methods=("PATCH",),
        description="Replace the existing icon",
    )
    @extend_schema(
        methods=("DELETE",),
        description="Delete the icon",
    )
    @action(methods=["post", "patch", "delete"], detail=True)
    def icon(self, request, pk):
        """
        Actions on the image for the given instance
        """
        # validate instance
        model = self.get_serializer().Meta.model
        attr = getattr(model, "icon", None)

        if attr is None:
            return Response(
                _("{} object has no attribute 'icon'.").format(model.__name__),
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = self.get_object()

        if self.request.method == "DELETE":
            return self._delete_image(model=model, instance=instance, pk=pk)

        serializer = ImageSerializer(data=request.data)

        if self.request.method == "POST":
            return self._post_image(
                model=model, instance=instance, serializer=serializer, pk=pk
            )
        else:
            return self._patch_image(
                model=model, instance=instance, serializer=serializer, pk=pk
            )

    def _post_image(self, model, instance, serializer, pk):
        """Create a new image"""

        # Not allow to update existing icon
        if instance.icon is not None:
            return Response(
                _("Icon attribute has been set on {} object (id: {}).").format(
                    model.__name__, pk
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            obj = serializer.save()

            # update instance when icon was None
            instance.icon = obj
            instance.save()

            return Response(self.get_serializer(instance).data)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def _patch_image(self, model, instance, serializer, pk):
        """Update the image"""

        # Not allow to update null icon
        if instance.icon is None:
            return Response(
                _(
                    "Icon attribute has not been set on {} object (id: {})."
                ).format(model.__name__, pk),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            # remove existing image
            instance.icon.delete()

            # create a new image
            obj = serializer.save()

            # update instance when icon was None
            instance.icon = obj
            instance.save()

            return Response(self.get_serializer(instance).data)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def _delete_image(self, model, instance, pk):
        """Delete the image"""

        if instance.icon is None:
            return Response(
                _(
                    "Icon attribute has not been set on {} object (id: {})."
                ).format(model.__name__, pk),
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.icon.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
