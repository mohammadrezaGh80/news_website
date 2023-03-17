from django.urls import path

from . import views

urlpatterns = [
    path('', views.report_list_view, name="report_list"),
    path('search/', views.report_search, name="report_search"),
    path('<int:pk>/', views.report_detail_view, name="report_detail"),
    path('create/', views.report_create_view, name="report_create"),
    path('<int:pk>/update/', views.report_update_view, name="report_update"),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name="report_delete"),
    path('<int:pk>/reply/<int:comment_id>/', views.reply_comment_view, name="reply_comment"),
    path('<int:pk>/update/<int:comment_id>/', views.comment_update_view, name="edit_comment"),
    path('<int:pk>/like/<int:comment_id>/', views.comment_like_view, name="like_comment"),
    path('<int:pk>/dislike/<int:comment_id>/', views.comment_dislike_view, name="dislike_comment"),
    path('pending/', views.report_pending_list_view, name="report_pending_list"),
    path('pending/search/', views.report_pending_search, name="report_pending_search"),
    path('pending/<int:pk>/', views.ReportPendingDetailView.as_view(), name="report_pending_detail"),
]
