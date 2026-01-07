from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from interact.permissions import AdminDelete
from interact.models import Search
from interact.serializers.search import SearchSerializer, SearchUpdateSerializer


# '/interact/searches'
class SearchViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, AdminDelete]

    def get_serializer_class(self):
        if self.action == 'update':
            return SearchUpdateSerializer
        return SearchSerializer

    def get_queryset(self):
        user = self.request.user
        return Search.objects.filter(user_id=user.id)

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}
