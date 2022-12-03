from django.db.models import Q
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

from .models import Report
from .forms import ReportForm, CommentForm


class ReportListView(generic.ListView):
    is_all_blank = False
    is_exist = True
    template_name = "news/report_list.html"
    context_object_name = "reports"
    extra_context = {"is_all_blank": is_all_blank,
                     "is_exist": is_exist}
    paginate_by = 4

    def get_queryset(self):
        return Report.objects.order_by("-datetime_modified")

    def post(self, request, *args, **kwargs):
        authors = get_user_model().objects.filter(
            username__contains=request.POST["search"]
        ) if "author-input" in request.POST else ''

        titles = Report.objects.filter(
            title__contains=request.POST["search"]
        ) if "title-input" in request.POST else ''

        if titles == '' and authors == '':
            self.is_all_blank = True
        elif not (titles or authors):
            self.is_exist = False

        reports = Report.objects.filter(
            Q(title__in=[*titles]) |
            Q(author__in=[*authors])
        ).order_by("-datetime_modified")

        return render(request,
                      self.template_name,
                      context={self.context_object_name: reports,
                               "is_all_blank": self.is_all_blank,
                               "is_exist": self.is_exist})


# def report_list_view(request):
#     if request.method == "POST":
#         authors = get_user_model().objects.filter(
#             username__contains=request.POST["search"]
#         ) if "author-input" in request.POST else ''
#
#         titles = Report.objects.filter(
#             title__contains=request.POST["search"]
#         ) if "title-input" in request.POST else ''
#
#         reports = Report.objects.filter(
#             Q(title__in=titles) |
#             Q(author__in=authors)
#         ).order_by("-datetime_modified")
#     else:
#         reports = Report.objects.order_by("-datetime_modified")
#     return render(request, "news/report_list.html", context={"reports": reports})


# class ReportDetailView(generic.DetailView):
#     model = Report
#     template_name = "news/report_detail.html"
#     context_object_name = "report"


def report_detail_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.report = report
            comment.save()
            comment_form = CommentForm()
    else:
        comment_form = CommentForm()

    return render(request, "news/report_detail.html",
                  context={"report": report,
                           "comment_form": comment_form,
                           "comments": report.comments.order_by("-datetime_created")})


# class ReportCreateView(generic.CreateView):
#     model = Report
#     fields = ["title", "description", "author"]
#     template_name = "news/report_create_and_update.html"


def report_create_view(request):
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
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
