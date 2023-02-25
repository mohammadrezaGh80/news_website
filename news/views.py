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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from datetime import datetime

from .models import Report, Comment, CommentRelation, UserLikeComment, UserDislikeComment, Category, ReportCategory
from .forms import ReportForm, CommentForm


class ReportListView(generic.ListView):
    template_name = "news/report_list.html"
    context_object_name = "reports"
    paginate_by = 4

    def get_queryset(self):
        return Report.report_published.order_by("-datetime_modified")

    def get_context_data(self, **kwargs):
        if self.request.session.get("search_info") is None:
            self.request.session["search_info"] = {"input_value": "", "title": "", "author": "",
                                                   "categories": {category.name: True for category in
                                                                  Category.objects.all()}}

        context = super(ReportListView, self).get_context_data(**kwargs)
        context["is_superuser"] = bool(self.request.user in get_user_model().objects.filter(is_superuser=True))
        context["categories"] = Category.objects.all()
        context["is_all_blank"] = False
        context["is_exist"] = True
        context["count_pending_reports"] = Report.objects.filter(status=Report.PENDING).count()
        context["all_categories_checked"] = [category_name for category_name, value in
                                             self.request.session["search_info"]["categories"].items() if value]
        context["is_title_exist"] = bool(self.request.session["search_info"]["title"])
        context["is_author_exist"] = bool(self.request.session["search_info"]["author"])
        context["input_value"] = self.request.session["search_info"]["input_value"]
        return context


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
        print(f"{list_selected_categories_id=}")
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

    def get_context_data(self, **kwargs):
        if self.request.session.get("pending_search_info") is None:
            self.request.session["pending_search_info"] = {
                "title": "", "author": "", "input_value": "",
                "categories": {category.name: True for category in Category.objects.all()}
            }

        context = super(ReportPendingListView, self).get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["is_all_blank"] = False
        context["is_exist"] = True
        context["all_categories_checked"] = [category_name for category_name, value in
                                             self.request.session["pending_search_info"]["categories"].items() if value]
        context["is_title_exist"] = bool(self.request.session["pending_search_info"]["title"])
        context["is_author_exist"] = bool(self.request.session["pending_search_info"]["author"])
        context["input_value"] = self.request.session["pending_search_info"]["input_value"]
        return context

    def test_func(self):
        return self.request.user in get_user_model().objects.filter(is_superuser=True)


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


def report_search(request):
    search_info = request.session.get("search_info")

    is_all_blank = False
    is_exist = True
    titles = []
    authors = []

    if request.method == "POST":
        if "title" in request.POST:
            search_info["title"] = request.POST["search"]
            titles = Report.report_published.filter(
                title__contains=search_info["title"]
            )
        else:
            search_info["title"] = ""

        if "author" in request.POST:
            search_info["author"] = request.POST["search"]
            authors = get_user_model().objects.filter(
                username__contains=search_info["author"]
            )
        else:
            search_info["author"] = ""

        search_info["input_value"] = request.POST["search"]
        request.session.modified = True

        for category in Category.objects.all():
            if category.name in request.POST:
                search_info["categories"][category.name] = True
            else:
                search_info["categories"][category.name] = False
        request.session.modified = True

    if search_info["title"]:
        titles = Report.report_published.filter(title__contains=search_info["title"])
    if search_info["author"]:
        authors = get_user_model().objects.filter(username__contains=search_info["author"])

    news = Report.report_published.filter(
        categories__category__name__in=[category_name for category_name in search_info["categories"] if
                                        search_info["categories"][category_name] is True]
    ).distinct().order_by("-datetime_modified")

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
        if search_info["title"] or search_info["author"]:
            is_exist = False
        else:
            reports = news

    paginator = Paginator(reports, 4)
    page = request.GET.get('page', 1)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request,
                  "news/report_list.html",
                  context={"reports": reports, "is_all_blank": is_all_blank,
                           "is_exist": is_exist, "categories": Category.objects.all(),
                           "is_superuser": bool(request.user in get_user_model().objects.filter(is_superuser=True)),
                           "page_obj": reports,
                           "is_title_exist": bool(search_info["title"]),
                           "is_author_exist": bool(search_info["author"]),
                           "count_pending_reports": Report.objects.filter(status=Report.PENDING).count(),
                           "input_value": search_info["input_value"],
                           "all_categories_checked": [category_name for category_name, value in
                                                      search_info["categories"].items() if value]})


@login_required
def report_pending_search(request):
    if request.user in get_user_model().objects.filter(is_superuser=True):

        pending_search_info = request.session.get("pending_search_info")

        is_all_blank = False
        is_exist = True
        titles = []
        authors = []

        if request.method == "POST":
            if "title" in request.POST:
                pending_search_info["title"] = request.POST["search"]
                titles = Report.objects.filter(
                    title__contains=pending_search_info["title"],
                    status=Report.PENDING,
                )
            else:
                pending_search_info["title"] = ""

            if "author" in request.POST:
                pending_search_info["author"] = request.POST["search"]
                authors = get_user_model().objects.filter(
                    username__contains=pending_search_info["author"]
                )
            else:
                pending_search_info["author"] = ""

            pending_search_info["input_value"] = request.POST["search"]
            request.session.modified = True

            for category in Category.objects.all():
                if category.name in request.POST:
                    pending_search_info["categories"][category.name] = True
                else:
                    pending_search_info["categories"][category.name] = False
            request.session.modified = True

        if pending_search_info["title"]:
            titles = Report.objects.filter(title__contains=pending_search_info["title"], status=Report.PENDING)
        if pending_search_info["author"]:
            authors = get_user_model().objects.filter(username__contains=pending_search_info["author"])

        news = Report.objects.filter(
            categories__category__name__in=[category_name for category_name in pending_search_info["categories"] if
                                            pending_search_info["categories"][category_name] is True]
        ).filter(status=Report.PENDING).distinct().order_by("-datetime_modified")

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
            if pending_search_info["title"] or pending_search_info["author"]:
                is_exist = False
            else:
                reports = news

        paginator = Paginator(reports, 4)
        page = request.GET.get('page', 1)

        try:
            reports = paginator.page(page)
        except PageNotAnInteger:
            reports = paginator.page(1)
        except EmptyPage:
            reports = paginator.page(paginator.num_pages)

        return render(request, "news/report_pending_list.html",
                      context={"reports_pending": reports,
                               "is_all_blank": is_all_blank,
                               "is_exist": is_exist,
                               "categories": Category.objects.all(),
                               "is_superuser": bool(request.user in get_user_model().objects.filter(is_superuser=True)),
                               "page_obj": reports,
                               "is_title_exist": bool(pending_search_info["title"]),
                               "is_author_exist": bool(pending_search_info["author"]),
                               "input_value": pending_search_info["input_value"],
                               "all_categories_checked": [category_name for category_name, value in
                                                          pending_search_info["categories"].items() if value]})
    raise PermissionDenied()


def get_reports_based_on_category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    reports = Report.report_published.filter(categories__category=category).order_by("-datetime_modified")

    paginator = Paginator(reports, 4)
    page = request.GET.get('page', 1)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request, "news/report_list.html",
                  context={"reports": reports,
                           "is_superuser": bool(request.user in get_user_model().objects.filter(is_superuser=True)),
                           "categories": Category.objects.all(),
                           "is_all_blank": False,
                           "is_exist": True,
                           "page_obj": reports,
                           "all_categories_checked": [category_name for category_name, value in
                                                      request.session["search_info"]["categories"].items() if value],
                           "is_title_exist": bool(request.session["search_info"]["title"]),
                           "is_author_exist": bool(request.session["search_info"]["author"]),
                           "input_value": request.session["search_info"]["input_value"]
                           })


def get_reports_pending_based_on_category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    reports = Report.objects.filter(categories__category=category, status=Report.PENDING).order_by("-datetime_modified")

    paginator = Paginator(reports, 4)
    page = request.GET.get('page', 1)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request, "news/report_pending_list.html",
                  context={"reports_pending": reports,
                           "categories": Category.objects.all(),
                           "is_all_blank": False,
                           "is_exist": True,
                           "page_obj": reports,
                           "all_categories_checked": [category_name for category_name, value in
                                                      request.session["pending_search_info"]["categories"].items() if
                                                      value],
                           "is_title_exist": bool(request.session["pending_search_info"]["title"]),
                           "is_author_exist": bool(request.session["pending_search_info"]["author"]),
                           "input_value": request.session["pending_search_info"]["input_value"]})
