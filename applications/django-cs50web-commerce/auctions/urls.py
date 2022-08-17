from django.urls import path

from . import views


app_name = 'auctions'
urlpatterns = [
    path('', views.AuctionsIndexView.as_view(), name='index'),
    path('/', views.AuctionsIndexView.as_view(), name='index_slash'),
    path('/category/<int:category_pk>', views.AuctionsIndexView.as_view(), name='category'),
    path('/auctioneers/<int:pk>', views.ProfileView.as_view(), name='profile'),
    path('/auctioneers/<int:pk>/history', views.UserHistoryView.as_view(), name='user_history'),
    path('/auctioneers/<int:pk>/watchlist', views.WatchlistView.as_view(), name='watchlist'),
    path('/auctioneers/<int:pk>/create_listing', views.CreateListingView.as_view(), name='create_listing'),
    path('/listings/<slug:slug>', views.ListingView.as_view(), name='listing'),
    path('/lots/<slug:slug>', views.AuctionLotView.as_view(), name='auction_lot'),
    path('/listings/<slug:slug>/comments', views.CommentsView.as_view(), name='comments'),
]
