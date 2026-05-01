from django.urls import path
from .views import *

urlpatterns = [
    
    #- Collections
    path("collections/", UserCollectionsView.as_view()),
    path("collections/create/", CreateCollectionView.as_view()),
    path("collections/<int:collection_id>/", CollectionDetailView.as_view()),
    path("collections/<int:collection_id>/delete/", DeleteCollectionView.as_view()),

    #- Items
    path("collections/add/", AddToCollectionView.as_view()),
    path("collections/<int:collection_id>/remove/<int:movie_id>/", RemoveFromCollectionView.as_view()),

    path("collection-items/<int:item_id>/toggle/", ToggleWatchedView.as_view()),

    path("collection-items/<int:item_id>/", CollectionItemDetailView.as_view()),
]