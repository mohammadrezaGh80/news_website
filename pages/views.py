from django.views import generic

from news.models import Report


class HomePageView(generic.ListView):
    template_name = "home.html"
    context_object_name = "last_news"

    def get_queryset(self):
        return Report.objects.filter(status=Report.PUBLISHED).order_by("-datetime_modified")[:3]

