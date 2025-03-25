from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('url-analyzer/', views.url_analyzer, name='url_analyzer'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('fetch-metrics/', views.fetch_metrics, name='fetch_metrics'),
    path('export-excel/', views.export_excel, name='export_excel'),
]
