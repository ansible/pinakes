"""A pagination implementation with page_size support"""

from rest_framework import pagination


class CatalogPageNumberPagination(pagination.PageNumberPagination):
    """Extend PageNumberPagination to take page_size from query"""

    page_size_query_param = "page_size"
    max_page_size = 100
