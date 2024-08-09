from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
     path('experiment/',
          views.ExperimentListCreateView.as_view(),
          name='experiment'),
     path('experiment/<int:experiment_id>/analysis/',
          views.AnalysisByExperimentListCreateView.as_view(),
          name='analysis-by-experiment-id'),
     path('analysis/',
          views.AnalysisListView.as_view(),
          name='analysis'),
     path('analysis/<int:id>/', 
         views.AnalysisByIdView.as_view(), 
         name='analysis-by-id'),
     path('analysis/<int:analysis_id>/alignment/',
          views.AnalysisAlignmentView.as_view(),
          name='analysis-alignment'),
     path('analysis/<int:analysis_id>/homology/',
          views.AnalysisHomologyView.as_view(),
          name='analysis-homology'),
     path('analysis/<int:analysis_id>/tree/',
          views.AnalysisTreeView.as_view(),
          name='analysis-tree-view'),
]