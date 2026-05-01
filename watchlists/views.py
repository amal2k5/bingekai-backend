from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Collection, CollectionItem
from .serializers import CollectionSerializer
from .services import add_movie_to_collection, remove_movie, toggle_watched 




#- COLLECTION 

class CreateCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")

        if not name:
            return Response(
                {"error": "Collection name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        collection, created = Collection.objects.get_or_create(
            user=request.user,
            name=name
        )

        return Response({
            "id": collection.id,
            "name": collection.name,
            "created": created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)



class UserCollectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        collections = Collection.objects.filter(
            user=request.user
        ).prefetch_related("items")

        serializer = CollectionSerializer(collections, many=True)
        return Response(serializer.data)



class CollectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, collection_id):
        collection = get_object_or_404(
            Collection,
            id=collection_id,
            user=request.user
        )

        serializer = CollectionSerializer(collection)
        return Response(serializer.data)



class DeleteCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, collection_id):
        collection = get_object_or_404(
            Collection,
            id=collection_id,
            user=request.user
        )

        collection.delete()

        return Response(
            {"status": "deleted"},
            status=status.HTTP_204_NO_CONTENT
        )


#- COLLECTION ITEMS (MOVIES)


class AddToCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        collection_id = request.data.get("collection_id")
        movie_id = request.data.get("movie_id")

        if not collection_id or not movie_id:
            return Response(
                {"error": "collection_id and movie_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = add_movie_to_collection(
            request.user,
            collection_id,
            movie_id
        )

        return Response({
            "status": "added" if created else "exists"
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)



class RemoveFromCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, collection_id, movie_id):
        remove_movie(
            request.user,
            collection_id,
            movie_id
        )

        return Response(
            {"status": "removed"},
            status=status.HTTP_200_OK
        )



class ToggleWatchedView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        is_watched = toggle_watched(
            request.user,
            item_id
        )

        return Response({
            "is_watched": is_watched
        }, status=status.HTTP_200_OK)




class CollectionItemDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        item = get_object_or_404(
            CollectionItem,
            id=item_id,
            collection__user=request.user
        )

        item.delete()

        return Response(
            {"status": "deleted"},
            status=status.HTTP_204_NO_CONTENT
        )