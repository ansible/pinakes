from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from main.catalog.serializers import ImageSerializer
from main.models import Image


class ImageMixin:
    """
    Image mixin shared with Catalog Portfolio and PortfolioItem
    """

    @extend_schema(
        request=ImageSerializer, responses=ImageSerializer, methods=("PATCH",)
    )
    @extend_schema(
        request=ImageSerializer,
        responses={201: ImageSerializer},
        methods=("POST",),
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

        instance = get_object_or_404(model, pk=pk)
        serializer = ImageSerializer(data=request.data)

        if self.request.method == "POST":
            return self.__post_image(
                model=model, instance=instance, serializer=serializer, pk=pk
            )
        elif self.request.method == "PATCH":
            return self.__patch_image(
                model=model, instance=instance, serializer=serializer, pk=pk
            )
        else:
            return self.__delete_image(
                model=model, instance=instance, serializer=serializer, pk=pk
            )

    def __post_image(self, model, instance, serializer, pk):
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
            # create image
            obj = Image.objects.create(
                file=self.request.data["icon"],
                source_ref=self.request.data["source_ref"],
            )
            obj.save()

            # update instance when icon is None
            instance.icon = obj
            instance.save()

            return Response(
                ImageSerializer(obj).data, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def __patch_image(self, model, instance, serializer, pk):
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
            old = Image.objects.get(id=instance.icon.id)
            old.delete()

            # create a new image
            obj = Image.objects.create(
                file=self.request.data["icon"],
                source_ref=self.request.data["source_ref"],
            )
            obj.save()

            # update instance when icon is None
            instance.icon = obj
            instance.save()

            return Response(ImageSerializer(obj).data)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def __delete_image(self, model, instance, serializer, pk):
        """Delete the image"""

        if instance.icon is None:
            return Response(
                _(
                    "Icon attribute has not been set on {} object (id: {})."
                ).format(model.__name__, pk),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            # remove existing image
            old = Image.objects.get(id=instance.icon.id)
            old.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
