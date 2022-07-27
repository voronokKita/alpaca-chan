from django.urls import path

from . import views


app_name = 'encyclopedia'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('/', views.IndexView.as_view(), name='index_slash'),
    path('/articles/<slug:slug>', views.DetailView.as_view(), name='detail'),
    path('/add-new-entry', views.AddNewEntry.as_view(), name='new_entry'),
    path('/edit/<slug:slug>', views.EditEntry.as_view(), name='edit_entry'),
    path('/delete/<slug:slug>', views.DeleteEntry.as_view(), name='delete_entry'),
]
