from django.views import generic

from .models import Report


class ReportListView(generic.ListView):
    model = Report
    template_name = "news/report_list.html"
    context_object_name = "reports"


class ReportDetailView(generic.DetailView):
    model = Report
    template_name = "news/report_detail.html"
    context_object_name = "report"
