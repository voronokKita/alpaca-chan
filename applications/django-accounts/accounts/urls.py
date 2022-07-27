from django.urls import path

from . import views


app_name = 'accounts'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('/', views.IndexView.as_view(), name='index_slash'),
    path('/<str:next>/register', views.RegisterView.as_view(), name='register'),
    path('/register', views.RegisterView.as_view(), name='register'),
    path('/<str:next>/login', views.LoginView.as_view(), name='login'),
    path('/login', views.LoginView.as_view(), name='login'),
    path('/<str:next>/logout', views.LogoutView.as_view(), name='logout'),
    path('/logout', views.LogoutView.as_view(), name='logout'),
]
