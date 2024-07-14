from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .serializers import AnalysisSerializer
from .models import Analysis
from injector import inject
from app.pagination import CustomPagination
from app.responses import WrappedResponse

class AnalysisByIdView(APIView):
    def get(self, request, id):
        return WrappedResponse(
            Analysis.objects.get(id=id), 
            AnalysisSerializer)
    
class AnalysisByToolView(ListAPIView):
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        tool_title = self.kwargs['tool']
        return Analysis.objects.filter(tools__title=tool_title).order_by('-id')
    
class AnalysisListView(ListAPIView):
    queryset = Analysis.objects.all().order_by('-id')
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination