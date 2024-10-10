from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.constants import BLASTN_EXCHANGE, BLASTN_ROUTING_KEY
from core.models import Analysis, AnalysisStatusChoices
from core.producers.rabbitmq_producer import RabbitmqPublisher
from core.serializers import AnalysisHomologyRequestSerializer


class AnalysisHomologyView(APIView):
    @transaction.atomic
    def post(self, request, analysis_id, *args, **kwargs):
        """Handles the POST request to add homology analysis to queue."""

        request_serializer = AnalysisHomologyRequestSerializer(
            data=request.data,
            context={'analysis_id': analysis_id})

        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status.HTTP_400_BAD_REQUEST)

        analysis = Analysis.objects.get(id=analysis_id)
        data = request_serializer.validated_data

        publisher = RabbitmqPublisher(exchange=BLASTN_EXCHANGE, routing_key=BLASTN_ROUTING_KEY)

        publisher.send_message({'analysis_id': analysis_id, **data})

        analysis.status = AnalysisStatusChoices.WAITING_FOR_EXECUTION
        analysis.save()

        return Response(data={"data": {"analysis_id": analysis_id,
                                       "message": "The blastn process is running"}},
                        status=status.HTTP_201_CREATED)