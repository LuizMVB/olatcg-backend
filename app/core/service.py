from .models import Analysis
from django.core.paginator import Paginator

class AnalysisFinderService:

    def find_all_in_sort_order(self, sort:str):
        if sort == 'ASC':
            return Analysis.objects.all().order_by('id')
        return Analysis.objects.all().order_by('-id')

    def find_by_id(self, id:int):
        return Analysis.objects.get(id=id)
    
    def find_all(self, number=1, per_page=15, sort='DESC'):
        analyses = self.find_all_in_sort_order(sort=sort)
        paginator = Paginator(object_list=analyses, 
                              per_page=per_page)
        page = paginator.get_page(number)
        page.sort = sort
        return page