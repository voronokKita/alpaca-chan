from django.urls import reverse
from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'auctions/index.html'

""" TODO
https://cs50.harvard.edu/web/2020/projects/2/commerce/

# MODELS
* Your application should have at least three models in addition to the User model: 
  one for auction listings, one for bids, and one for comments made on auction listings.

# ACTIVE LISTINGS PAGE
* The default route of your web application should let users view all of the currently active auction listings. 
  For each active listing, this page should display the title, description, current price, and photo.
  
* The page should display a list of categories, clicking on any of which will display the items in that category.

# USER PAGE
* A user must be able to register and then log in with his username and password.

# CREATE LISTING
* Users should be able to visit a page to create a new listing. 
  They should be able to specify a title for the listing, a text-based description, and what the starting bid should be, 
  provide an image for the listing and  a category - e.g. Fashion, Toys, Electronics, Home, etc.

# LISTING PAGE
* On that page, users should be able to view all details about the listing, including the current price for the listing.

* If the user is signed in, the user should be able to add the item to their “Watchlist.” 
  If the item is already on the watchlist, the user should be able to remove it.
    
* If the user is signed in, the user should be able to bid on the item. 
  The bid must be at least as large as the starting bid, and must be greater than any other bids 
  that have been placed. If the bid doesn’t meet those criteria, the user should be presented with an error.
    
* If the user is signed in and is the one who created the listing, 
  the user should have the ability to “close” the auction from this page, 
  which makes the highest bidder the winner of the auction and makes the listing no longer active.
    
* If a user is signed in on a closed listing page, and the user has won that auction, the page should say so.
  Users who are signed in should be able to add comments to the listing page. 
  The listing page should display all comments that have been made on the listing.

# WATCHLIST
* Users who are signed in should be able to visit a Watchlist page, 
  which should display all of the listings that a user has added to their watchlist. 
  Clicking on any of those listings should take the user to that listing’s page.

* The page should display all of the listings that are owned by the user: created and purchased.

# NOTIFICATION PAGE
* A registered user can go to the page and read notifications about closed auctions.
  
# DJANGO ADMIN INTERFACE
* Via the Django admin interface, a site administrator should be able to view, 
  add, edit, and delete any listings, comments, and bids made on the site.
"""
