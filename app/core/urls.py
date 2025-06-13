from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter
from .views import ExperimentViewSet, AnalysisViewSet

router = SimpleRouter()
router.register(r'experiment', ExperimentViewSet)

nested_router = NestedSimpleRouter(router, r'experiment', lookup='experiment')
nested_router.register(r'analysis', AnalysisViewSet, basename='experiment-analysis')

urlpatterns = router.urls + nested_router.urls