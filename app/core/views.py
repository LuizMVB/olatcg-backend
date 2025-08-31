from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from .models import Experiment, Analysis, AnalysisStatusChoices, AnalysisInput, AnalysisOutput
from .serializers import ExperimentSerializer, AnalysisSerializer, UserSerializer
from .filters import ExperimentFilter, AnalysisFilter
from .strategy_factory import StrategyFactory
from .strategies import ExecutionType
from .authentication import ExpiringTokenAuthentication 

# ===================== AUTHENTICATION =======================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token_key = response.data.get('token') if response.data else None
        if not token_key:
            return Response({'error': 'Invalid token response'}, status=status.HTTP_400_BAD_REQUEST)
        token = Token.objects.get(key=token_key)
        return Response({
            'token': token.key,
            'user_id': token.user.id,
            'username': token.user.username
        })


# ===================== EXPERIMENTS =======================

class ExperimentViewSet(viewsets.ModelViewSet):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExperimentSerializer
    filterset_class = ExperimentFilter
    ordering_fields = ['id', 'created_at']
    ordering = ['-id']

    def get_queryset(self):
        return Experiment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ===================== ANALYSIS =======================

class AnalysisViewSet(viewsets.ModelViewSet):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer
    filterset_class = AnalysisFilter
    ordering_fields = ['id']
    ordering = ['-id']

    def get_queryset(self):
        experiment_id = self.kwargs.get('experiment_pk')
        return Analysis.objects.filter(
            experiment__id=experiment_id,
            experiment__user=self.request.user
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        experiment_id = self.kwargs.get('experiment_pk')
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis: Analysis = serializer.save(experiment=experiment)

        try:
            strategy = StrategyFactory.get_strategy(analysis.type)
            execution = strategy.execute(analysis)

            if execution.type is ExecutionType.ASYNC:
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            analysis.status = AnalysisStatusChoices.SUCCEEDED
            analysis.save(update_fields=['status'])

            analysis_input = AnalysisInput.objects.create(
                command=execution.command,
                analysis=analysis,
            )

            AnalysisOutput.objects.create(
                results=execution.result,
                file=execution.file,
                input=analysis_input,
            )

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            analysis.status = AnalysisStatusChoices.FAILED
            analysis.save(update_fields=['status'])
            raise e