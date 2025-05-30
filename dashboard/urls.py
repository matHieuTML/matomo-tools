from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('url-analyzer/', views.url_analyzer, name='url_analyzer'),
    path('verify-matomo-config/', views.verify_matomo_config, name='verify_matomo_config'),
    path('fetch-metrics/', views.fetch_metrics, name='fetch_metrics'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('proxy-matomo/', views.proxy_matomo_api, name='proxy_matomo'),
]
