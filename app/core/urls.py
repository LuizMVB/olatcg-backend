from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter
from .views import ExperimentViewSet, AnalysisViewSet, RegisterView, LoginView

router = SimpleRouter()
router.register(r'experiment', ExperimentViewSet, basename='experiment')  # <- fix aqui

nested_router = NestedSimpleRouter(router, r'experiment', lookup='experiment')
nested_router.register(r'analysis', AnalysisViewSet, basename='experiment-analysis')

auth_urls = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]

urlpatterns = auth_urls + router.urls + nested_router.urls