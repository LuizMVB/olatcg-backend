from rest_framework.response import Response
from rest_framework import status

class WrappedResponse(Response):

    def __init__(self, domain_object, serializer_class, many=False, **kwargs):
        serialized = serializer_class(domain_object, many=many)
        super().__init__(data={'data': serialized.data}, status=status.HTTP_200_OK, **kwargs)
