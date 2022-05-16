from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .serializers import TagSerializer
from .exception_handler import get_object_by_id_or_404


class TagMixin:
    """
    Tag mixin shared with Approval, Catalog and Inventory
    """

    @extend_schema(
        responses={200: TagSerializer(many=True)},
    )
    @action(methods=["get"], detail=True)
    def tags(self, request, pk):
        """
        List all tags of a given instance
        """
        model = self.get_serializer().Meta.model
        instance = get_object_by_id_or_404(model, pk)
        tags = instance.tags.all().order_by("name")

        page = self.paginate_queryset(tags)
        if page is not None:
            serializer = TagSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        data = TagSerializer(tags, many=True).data

        return Response(data)

    @extend_schema(request=TagSerializer, responses={201: TagSerializer})
    @action(methods=["post"], detail=True)
    def tag(self, request, pk):
        """
        Add a tag to a given instance:
            content body:    {"name": "tag"}
        """
        model = self.get_serializer().Meta.model
        instance = get_object_by_id_or_404(model, pk)

        tag_serializer = TagSerializer(data=request.data)
        if tag_serializer.is_valid():
            instance.tags.add(request.data["name"])
            return Response(
                tag_serializer.data, status=status.HTTP_201_CREATED
            )

        return Response(
            tag_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        request=TagSerializer,
        responses={204: None},
    )
    @action(methods=["post"], detail=True)
    def untag(self, request, pk):
        """
        Remove the tag from a given instance:
            content body:    {"name": "tag"}
        """
        model = self.get_serializer().Meta.model
        instance = get_object_by_id_or_404(model, pk)

        tag_serializer = TagSerializer(data=request.data)
        if tag_serializer.is_valid():
            instance.tags.remove(request.data["name"])
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        return Response(
            tag_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
