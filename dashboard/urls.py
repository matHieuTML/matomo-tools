from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('fetch-metrics/', views.fetch_metrics, name='fetch_metrics'),
]
