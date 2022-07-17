from django.urls import path

from . import views


app_name = 'encyclopedia'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('/', views.IndexView.as_view(), name='index'),
    path('/articles/<int:pk>', views.DetailView.as_view(), name='detail'),
    path('/add-new-entry', views.AddNewEntry.as_view(), name='new_entry'),
]
