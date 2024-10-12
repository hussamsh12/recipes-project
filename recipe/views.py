"""
Views for the recipe APIs
"""


from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Recipe, Tag, Ingredient

from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """A ViewSet for managing Recipe APIs"""

    serializer_class = serializers.RecipeDetailsSerializer
    queryset = Recipe.objects.all()

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieves recipes for authenticated user"""

        return self.queryset.filter(user=self.request.user).order_by('-id')


    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
        return self.serializer_class


    def perform_create(self, serializer):
        """Creates a new recipe"""
        serializer.save(user=self.request.user)


class TagViewSet(mixins.ListModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """ A ViewSet for managing our tags"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieves tags for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')



class IngredientViewSet(mixins.ListModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    """A ViewSet for managing Ingredients"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieves Ingredients for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')


