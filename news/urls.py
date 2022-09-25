from django.urls import path

from . import views

urlpatterns = [
    path('', views.ReportListView.as_view(), name="report_list"),
    path('<int:pk>/', views.ReportDetailView.as_view(), name="report_detail"),
    path('create/', views.ReportCreateView.as_view(), name="report_create"),
    path('<int:pk>/update/', views.ReportUpdateView.as_view(), name="report_update"),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name="report_delete"),
]
