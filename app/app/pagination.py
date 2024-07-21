from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

class CustomPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'total_pages': self.page.paginator.count,
            },
            'data': data,
            'links': {
                'self': self.request.build_absolute_uri(),
                'first': self.get_first_link(),
                'prev': self.get_previous_link(),
                'next': self.get_next_link(),
                'last': self.get_last_link()
            },
        })
    
    def get_first_link(self):
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self):
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, self.page.paginator.num_pages)