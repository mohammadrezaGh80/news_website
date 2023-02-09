from django.db.models import Q
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from datetime import datetime

from .models import Report, Comment, CommentRelation, UserLikeComment, UserDislikeComment, Category
from .forms import ReportForm, CommentForm


class ReportListView(generic.ListView):
    template_name = "news/report_list.html"
    context_object_name = "reports"
    paginate_by = 4

    def get_queryset(self):
        return Report.report_published.order_by("-datetime_modified")

    def get_context_data(self, **kwargs):
        context = super(ReportListView, self).get_context_data(**kwargs)
        context["is_superuser"] = bool(self.request.user in get_user_model().objects.filter(is_superuser=True))
        context["categories"] = Category.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        is_all_blank = False
        is_exist = True
        authors = get_user_model().objects.filter(
            username__contains=request.POST["search"]
        ) if "author" in request.POST else ''

        titles = Report.report_published.filter(
            title__contains=request.POST["search"]
        ) if "title" in request.POST else ''

        news = list()
        for category in Category.objects.all():
            news.extend(Report.report_published.filter(
                categories__category__name=category.name
            )) if f"{category.name}" in request.POST else ''

        news = list(sorted(set(news), key=lambda report: report.datetime_modified, reverse=True))

        if titles == '' and authors == '' and not news:
            is_all_blank = True
        elif not (titles or authors or news) or not news:
            is_exist = False

        reports = Report.report_published.filter(
            Q(title__in=[*titles]) |
            Q(author__in=[*authors])
        ).order_by("-datetime_modified")

        if reports:
            if exist_reports := list(set(news) & {*reports}):
                reports = list(sorted(exist_reports, key=lambda report: report.datetime_modified, reverse=True))
            else:
                reports = list()
                is_exist = False
        else:
            if "title" in request.POST or "author" in request.POST:
                is_exist = False
            else:
                reports = news

        return render(request,
                      self.template_name,
                      context={self.context_object_name: reports,
                               "is_all_blank": is_all_blank,
                               "is_exist": is_exist,
                               "categories": Category.objects.all(),
                               "is_superuser": bool(self.request.user in get_user_model().objects.filter(is_superuser=True))})


def report_detail_view(request, pk):
    list_id_like_comment = list()
    list_id_dislike_comment = list()
    report = get_object_or_404(Report.objects.filter(status=Report.PUBLISHED), pk=pk)
    if request.user.is_authenticated:
        list_user_like_comments = UserLikeComment.objects.filter(user=request.user, comment__report=report)
        list_user_dislike_comments = UserDislikeComment.objects.filter(user=request.user, comment__report=report)
        list_id_like_comment = [user_like_comment.comment.pk for user_like_comment in list_user_like_comments]
        list_id_dislike_comment = [user_dislike_comment.comment.pk
                                   for user_dislike_comment in list_user_dislike_comments]
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.report = report
            comment.datetime_modified = datetime.now()
            comment.save()
            messages.success(request, "دیدگاه شما با موفقیت ثبت شد.")
            comment_form = CommentForm()
        else:
            error_labels = [field.label for field in comment_form for _ in field.errors]
            if "Text" in error_labels:
                messages.error(request, "محتوایی برای دیدگاه وجود ندارد...")
            if "Captcha" in error_labels:
                messages.error(request, "کپچا تیک زده نشده است...")

    else:
        comment_form = CommentForm()

    return render(request, "news/report_detail.html",
                  context={"report": report,
                           "comment_form": comment_form,
                           "comments": report.comments.order_by("-datetime_created"),
                           "list_id_like_comment": list_id_like_comment,
                           "list_id_dislike_comment": list_id_dislike_comment,
                           "report_categories": report.categories.all()})


def report_create_view(request):
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()
            messages.success(request, "خبر شما برای تایید ارسال شد.")
            return redirect("report_list")
        else:
            error_labels = [field.label for field in form for _ in field.errors]
            if "Title" in error_labels:
                messages.error(request, "عنوانی برای خبر وجود ندارد...")
            if "Description" in error_labels:
                messages.error(request, "توضیحاتی برای خبر وجود ندارد...")

    else:
        form = ReportForm()
    return render(request, "news/report_create_and_update.html", context={"form": form})


class ReportUpdateView(LoginRequiredMixin,  generic.UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "news/report_create_and_update.html"

    def form_valid(self, form):
        report = self.object
        messages.success(self.request, f'خبر "{report.title}" با موفقیت تغییر یافت.')
        return super(ReportUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        error_labels = [field.label for field in form for _ in field.errors]
        if "Title" in error_labels:
            messages.error(self.request, "عنوانی برای خبر وجود ندارد...")
        if "Description" in error_labels:
            messages.error(self.request, "توضیحاتی برای خبر وجود ندارد...")
        return super(ReportUpdateView, self).form_invalid(form)


class ReportDeleteView(LoginRequiredMixin,  generic.DeleteView):
    model = Report
    template_name = "news/report_delete.html"
    success_url = reverse_lazy("report_list")

    def form_valid(self, form):
        report = self.object
        messages.success(self.request, f'خبر "{report.title}" با موفقیت حذف شد.')
        return super(ReportDeleteView, self).form_valid(form)


@login_required
def reply_comment_view(request, pk, comment_id):
    report = get_object_or_404(Report, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.user = request.user
            new_comment.report = report
            new_comment.datetime_modified = datetime.now()
            new_comment.save()
            messages.success(request, f"دیدگاه شما برای پاسخ به {comment.user.username} با موفقیت ثبت شد.")
            CommentRelation.objects.create(reply=new_comment, reply_to=comment)
            return redirect("report_detail", report.id)
        else:
            error_labels = [field.label for field in comment_form for _ in field.errors]
            if "Text" in error_labels:
                messages.error(request, "محتوایی برای دیدگاه وجود ندارد...")
            if "Captcha" in error_labels:
                messages.error(request, "کپچا تیک زده نشده است...")
            return redirect("reply_comment", report.id, comment.id)
    else:
        comment_form = CommentForm()
    return render(request, "news/reply_comment.html",
                  context={"to_comment": comment,
                           "comment": comment.get_root_comment(),
                           "report": report,
                           "comment_form": comment_form,
                           "count_comments": Comment.objects.filter(report_id=report.id).count()})


@login_required
def comment_update_view(request, pk, comment_id):
    report = get_object_or_404(Report, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user == request.user:
        comment_form = CommentForm(request.POST or None, instance=comment)
        if request.method == "POST":
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.datetime_modified = datetime.now()
                comment.save()
                messages.success(request, "پیام شما با موفقیت تغییر یافت.")
                return redirect("report_detail", report.id)
            else:
                error_labels = [field.label for field in comment_form for _ in field.errors]
                if "Text" in error_labels:
                    messages.error(request, "محتوایی برای دیدگاه وجود ندارد...")
                if "Captcha" in error_labels:
                    messages.error(request, "کپچا تیک زده نشده است...")
                return redirect("edit_comment", report.id, comment.id)

        return render(request, "news/reply_comment.html",
                      context={"comment": comment.get_root_comment(),
                               "report": report,
                               "comment_form": comment_form})
    else:
        raise PermissionDenied()


@login_required
def comment_like_view(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == "POST":
        try:
            user_like_comment = UserLikeComment.objects.get(user=request.user, comment=comment)
        except UserLikeComment.DoesNotExist:
            comment.likes += 1
            comment.save()
            UserLikeComment.objects.create(user=request.user, comment=comment)
        else:
            user_like_comment.delete()
            comment.likes -= 1
            comment.save()

        return JsonResponse({"likes": comment.likes})


@login_required
def comment_dislike_view(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == "POST":
        try:
            user_dislike_comment = UserDislikeComment.objects.get(user=request.user, comment=comment)
        except UserDislikeComment.DoesNotExist:
            comment.dislikes += 1
            comment.save()
            UserDislikeComment.objects.create(user=request.user, comment=comment)
        else:
            user_dislike_comment.delete()
            comment.dislikes -= 1
            comment.save()

        return JsonResponse({"dislikes": comment.dislikes})


class ReportPendingListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    template_name = "news/report_pending_list.html"
    context_object_name = "reports_pending"
    paginate_by = 4

    def get_queryset(self):
        return Report.objects.filter(status=Report.PENDING).order_by("-datetime_modified")

    def test_func(self):
        return self.request.user in get_user_model().objects.filter(is_superuser=True)

    def get_context_data(self, **kwargs):
        context = super(ReportPendingListView, self).get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        is_all_blank = False
        is_exist = True
        authors = get_user_model().objects.filter(
            username__contains=request.POST["search"]
        ) if "author" in request.POST else ''

        titles = Report.objects.filter(
            title__contains=request.POST["search"],
            status=Report.PENDING
        ) if "title" in request.POST else ''

        news = list()
        for category in Category.objects.all():
            news.extend(Report.objects.filter(
                categories__category__name=category.name,
                status=Report.PENDING
            )) if f"{category.name}" in request.POST else ''

        news = list(sorted(set(news), key=lambda report: report.datetime_modified, reverse=True))

        if titles == '' and authors == '' and not news:
            is_all_blank = True
        elif not (titles or authors or news) or not news:
            is_exist = False

        reports = Report.objects.filter(
            Q(title__in=[*titles]) |
            Q(author__in=[*authors])
        ).filter(status=Report.PENDING).order_by("-datetime_modified")

        if reports:
            if exist_reports := list(set(news) & {*reports}):
                reports = list(sorted(exist_reports, key=lambda report: report.datetime_modified, reverse=True))
            else:
                reports = list()
                is_exist = False
        else:
            if "title" in request.POST or "author" in request.POST:
                is_exist = False
            else:
                reports = news

        return render(request,
                      self.template_name,
                      context={self.context_object_name: reports,
                               "is_all_blank": is_all_blank,
                               "is_exist": is_exist,
                               "categories": Category.objects.all(),
                               "is_superuser": bool(
                                   self.request.user in get_user_model().objects.filter(is_superuser=True))})


class ReportPendingDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    template_name = "news/report_pending_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        return Report.objects.filter(status=Report.PENDING)

    def test_func(self):
        return self.request.user in get_user_model().objects.filter(is_superuser=True)

    def get_context_data(self, **kwargs):
        context = super(ReportPendingDetailView, self).get_context_data(**kwargs)
        report = self.get_object()
        context["report_categories"] = report.categories.all()
        return context

    def post(self, request, *args, **kwargs):
        report = self.get_object()
        if request.POST["confirm"] == "yes":
            report.status = Report.PUBLISHED
            report.save()
            messages.success(request, f'خبر "{report.title}" تایید شد.')
            return redirect("report_list")
        elif request.POST["confirm"] == "no":
            report.status = Report.CANCELED
            report.save()
            messages.error(request, f'خبر "{report.title}" رد شد.')
            return redirect("report_pending_list")
