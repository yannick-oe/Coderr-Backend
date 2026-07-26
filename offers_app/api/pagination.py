"""Pagination for the offers_app list endpoint."""

from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE_SIZE = 6
MAX_PAGE_SIZE = 100


class OfferPagination(PageNumberPagination):
    """Six offers per page, matching the frontend PAGE_SIZE.

    Attached to the offer list view only; pagination is never enabled
    globally, so profiles, reviews and orders stay bare arrays.
    """

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = MAX_PAGE_SIZE

    def get_page_number(self, request, paginator):
        """Treat an empty or missing page value as the first page."""
        if not request.query_params.get(self.page_query_param):
            return 1
        return super().get_page_number(request, paginator)
