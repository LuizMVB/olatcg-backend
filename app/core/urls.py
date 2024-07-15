from django.urls import path
from core.views import AnalysisByIdView, AnalysisListView

urlpatterns = [
     path('analysis/<int:id>/', 
         AnalysisByIdView.as_view(), 
         name='analysis-by-id'),
     path('analysis/',
          AnalysisListView.as_view(),
          name='analysis-paginated'),
]