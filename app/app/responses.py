from rest_framework.response import Response
from rest_framework import status

class WrappedResponse(Response):
    def __init__(self, data=None, status=None, serializer_class=None, **kwargs):
        if serializer_class and data is not None:
            serialized = serializer_class(data, many=isinstance(data, list))
            data = {'data': serialized.data}
        super().__init__(data=data, status=status, **kwargs)