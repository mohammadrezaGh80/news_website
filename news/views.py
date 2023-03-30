from django.db.models import Q
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST

from datetime import datetime

from .models import Report, Comment, CommentRelation, UserLikeComment, UserDislikeComment, Category, ReportCategory
from .forms import ReportForm, CommentForm


def report_list_view(request):
    is_exist = False

    q = request.GET.get('q', '')
    title = request.GET.get('title')
    author = request.GET.get('author')
    sport = request.GET.get('sport')
    football = request.GET.get('football')
    political = request.GET.get('political')
    internal = request.GET.get('internal')
    foreign = request.GET.get('foreign')
    exclusive = request.GET.get('exclusive')

    dict_filters = {"title": title, "author": author, "sport": sport,
                    "football": football, "political": political,
                    "internal": internal, "foreign": foreign, "exclusive": exclusive}

    if not title and not author:
        dict_filters['title'], dict_filters['author'] = 'true', 'true'

    if q:
        queryset_reports = Report.report_published.filter(
            Q(title__contains=q if dict_filters['title'] else []) |
            Q(author__username__contains=q if dict_filters['author'] else []))
    else:
        queryset_reports = Report.report_published

    dict_categories = {"sport": sport, "football": football, "political": political,
                       "internal": internal, "foreign": foreign, "exclusive": exclusive}

    for item_filter in dict_filters.values():
        if item_filter not in [None, 'true']:
            raise Http404()

    all_categories_select_name = [item for item in dict_categories if dict_categories[item]]

    reports = queryset_reports.filter(
        categories__category__name__in=all_categories_select_name if all_categories_select_name
        else [*dict_categories.keys()]
    ).distinct().order_by("-datetime_modified")

    if reports.exists():
        is_exist = True

    paginator = Paginator(reports, 4)
    page = request.GET.get('page')

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request, "news/report_list.html", context={
        "reports": reports,
        "page_obj": reports,
        "is_superuser": bool(request.user in get_user_model().objects.filter(is_superuser=True)),
        "categories": Category.objects.all(),
        "is_exist": is_exist,
        "count_pending_reports": Report.objects.filter(status=Report.PENDING).count(),
        "dict_filters": dict_filters
    })


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
        list_categories_id = request.POST.getlist("category") if "category" in request.POST else None
        if form.is_valid() and list_categories_id:
            report = form.save(commit=False)
            report.author = request.user
            if request.user in get_user_model().objects.filter(is_superuser=True):
                report.status = Report.PUBLISHED
                messages.success(request, f'خبر "{report.title}" بارگزاری شد.')
            else:
                messages.success(request, "خبر شما برای تایید ارسال شد.")
            report.save()

            for category_id in list_categories_id:
                ReportCategory.objects.create(report=report, category=Category.objects.get(pk=category_id))

            return redirect("report_list")
        else:
            error_labels = [field.label for field in form for _ in field.errors]
            if "Title" in error_labels:
                messages.error(request, "عنوانی برای خبر وجود ندارد...")
            if "Description" in error_labels:
                messages.error(request, "توضیحاتی برای خبر وجود ندارد...")

    else:
        form = ReportForm()
    return render(request, "news/report_create_and_update.html",
                  context={"form": form, "categories": Category.objects.all()})


def report_update_view(request, pk):
    if request.user.is_authenticated:
        report = get_object_or_404(Report, pk=pk)
        selected_categories = Category.objects.filter(reports__report=report)
        list_selected_categories_id = [category.id for category in selected_categories]
        if request.method == "POST":
            form = ReportForm(request.POST, request.FILES, instance=report)
            list_categories_id = list(
                map(int, request.POST.getlist("category"))) if "category" in request.POST else None
            if form.is_valid() and list_categories_id:
                form.save()
                messages.success(request, f'خبر "{report.title}" با موفقیت تغییر یافت.')

                for category_id in list_categories_id:
                    if category_id not in list_selected_categories_id:
                        ReportCategory.objects.create(report=report, category=Category.objects.get(pk=category_id))

                for category_id in list_selected_categories_id:
                    if category_id not in list_categories_id:
                        report_category = ReportCategory.objects.get(report=report,
                                                                     category=Category.objects.get(pk=category_id))
                        report_category.delete()

                return redirect("report_detail", report.pk)
            else:
                error_labels = [field.label for field in form for _ in field.errors]
                if "Title" in error_labels:
                    messages.error(request, "عنوانی برای خبر وجود ندارد...")
                if "Description" in error_labels:
                    messages.error(request, "توضیحاتی برای خبر وجود ندارد...")
        else:
            form = ReportForm(instance=report)
        return render(request, "news/report_create_and_update.html",
                      context={"report": report,
                               "form": form,
                               "categories": Category.objects.all(),
                               "all_selected_categories": selected_categories})

    raise PermissionDenied()


class ReportUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "news/report_create_and_update.html"

    def get_context_data(self, **kwargs):
        context = super(ReportUpdateView, self).get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["all_selected_categories"] = Category.objects.filter(reports__report=self.get_object())
        return context

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


class ReportDeleteView(LoginRequiredMixin, generic.DeleteView):
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
@require_POST
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
@require_POST
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


def report_pending_list_view(request):
    is_exist = False

    q = request.GET.get('q', '')
    title = request.GET.get('title')
    author = request.GET.get('author')
    sport = request.GET.get('sport')
    football = request.GET.get('football')
    political = request.GET.get('political')
    internal = request.GET.get('internal')
    foreign = request.GET.get('foreign')
    exclusive = request.GET.get('exclusive')

    dict_filters = {"title": title, "author": author, "sport": sport,
                    "football": football, "political": political,
                    "internal": internal, "foreign": foreign, "exclusive": exclusive}

    if not title and not author:
        dict_filters['title'], dict_filters['author'] = 'true', 'true'

    if q:
        queryset_reports = Report.objects.filter(status=Report.PENDING).filter(
            Q(title__contains=q if dict_filters['title'] else []) |
            Q(author__username__contains=q if dict_filters['author'] else []))
    else:
        queryset_reports = Report.objects.filter(status=Report.PENDING)

    dict_categories = {"sport": sport, "football": football, "political": political,
                       "internal": internal, "foreign": foreign, "exclusive": exclusive}

    for item_filter in dict_filters.values():
        if item_filter not in [None, 'true']:
            raise Http404()

    all_categories_select_name = [item for item in dict_categories if dict_categories[item]]

    reports = queryset_reports.filter(
        categories__category__name__in=all_categories_select_name if all_categories_select_name
        else [*dict_categories.keys()]
    ).distinct().order_by("-datetime_modified")

    if reports.exists():
        is_exist = True

    paginator = Paginator(reports, 4)
    page = request.GET.get('page')

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request, "news/report_pending_list.html", context={
        "reports_pending": reports,
        "page_obj": reports,
        "categories": Category.objects.all(),
        "is_exist": is_exist,
        "dict_filters": dict_filters
    })


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
