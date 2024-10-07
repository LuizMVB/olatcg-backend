from django.urls import path
from core.views.analysis_alignment_view import *
from core.views.analysis_by_experiment_list_create_view import *
from core.views.analysis_by_id_view import *
from core.views.analysis_homology_view import *
from core.views.analysis_list_view import *
from core.views.analysis_tree_view import *
from core.views.experiment_list_create_view import *

urlpatterns = [
     path('experiment/',
          ExperimentListCreateView.as_view(),
          name='experiment'),
     path('experiment/<int:experiment_id>/analysis/',
          AnalysisByExperimentListCreateView.as_view(),
          name='analysis-by-experiment-id'),
     path('analysis/',
          AnalysisListView.as_view(),
          name='analysis'),
     path('analysis/<int:id>/', 
         AnalysisByIdView.as_view(),
         name='analysis-by-id'),
     path('analysis/<int:analysis_id>/alignment/',
          AnalysisAlignmentView.as_view(),
          name='analysis-alignment'),
     path('analysis/<int:analysis_id>/homology/',
          AnalysisHomologyView.as_view(),
          name='analysis-homology'),
     path('analysis/<int:analysis_id>/tree/',
          AnalysisTreeView.as_view(),
          name='analysis-tree-view'),
]