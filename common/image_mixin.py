from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from main.catalog.serializers import ImageSerializer
from main.models import Image


class ImageMixin:
    """
    Image mixin shared with Catalog Portfolio and PortfolioItem
    """

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
            # Not allow to update existing icon
            if instance.icon is not None:
                return Response(
                    _("Icon attribute has been set on {} object (id: {pk}).").format(
                        model.__name__
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if serializer.is_valid():
                # create image
                obj = Image.objects.create(
                    file=request.data["icon"], source_ref=request.data["source_ref"]
                )
                obj.save()

                # update instance when icon is None
                instance.icon = obj
                instance.save()

                return Response(status=status.HTTP_201_CREATED)
        elif self.request.method == "PATCH":
            # Not allow to update null icon
            if instance.icon is None:
                return Response(
                    _("Icon attribute has not been set on {} object (id: {}).").format(
                        model.__name__, pk
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if serializer.is_valid():
                # remove existing image
                old = Image.objects.get(id=instance.icon.id)
                old.delete()

                # create a new image
                obj = Image.objects.create(
                    file=request.data["icon"], source_ref=request.data["source_ref"]
                )
                obj.save()

                # update instance when icon is None
                instance.icon = obj
                instance.save()

                return Response(status=status.HTTP_201_CREATED)
        elif self.request.method == "DELETE":
            if instance.icon is None:
                return Response(
                    _("Icon attribute has not been set on {} object (id: {}).").format(
                        model.__name__, pk
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if serializer.is_valid():
                # remove existing image
                old = Image.objects.get(id=instance.icon.id)
                old.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                _("{} is not supported on {}.").format(
                    self.request.method, model.__name__
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
