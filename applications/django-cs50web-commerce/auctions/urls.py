from django.urls import path

from . import views


app_name = 'auctions'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('/', views.IndexView.as_view(), name='index_slash'),
]
