from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import render, redirect

from .models import Report
from .forms import ReportForm


class ReportListView(generic.ListView):
    template_name = "news/report_list.html"
    context_object_name = "reports"

    def get_queryset(self):
        return Report.objects.order_by("-datetime_modified")


class ReportDetailView(generic.DetailView):
    model = Report
    template_name = "news/report_detail.html"
    context_object_name = "report"


# class ReportCreateView(generic.CreateView):
#     model = Report
#     fields = ["title", "description", "author"]
#     template_name = "news/report_create_and_update.html"

def report_create_view(request):
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()
            return redirect("report_detail", report.id)
    else:
        form = ReportForm()
    return render(request, "news/report_create_and_update.html", context={"form": form})


class ReportUpdateView(generic.UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "news/report_create_and_update.html"


class ReportDeleteView(generic.DeleteView):
    model = Report
    template_name = "news/report_delete.html"
    success_url = reverse_lazy("report_list")
