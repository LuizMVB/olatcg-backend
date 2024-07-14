from django.urls import path
from core.views import AnalysisByIdView, AnalysisListView, AnalysisByToolView

urlpatterns = [
     path('analysis/<int:id>/', 
         AnalysisByIdView.as_view(), 
         name='analysis-by-id'),
     path('analysis/',
          AnalysisListView.as_view(),
          name='analysis-paginated'),
     path('analysis/<str:tool>/tool/',
          AnalysisByToolView.as_view(),
          name='analysis-by-tool'),
]