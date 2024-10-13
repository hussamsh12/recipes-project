"""
Views for the recipe APIs
"""

from drf_spectacular.utils import (extend_schema_view,
                                   extend_schema,
                                   OpenApiParameter,
                                   OpenApiTypes)

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Recipe, Tag, Ingredient

from recipe import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of Ids to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of Ids to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """A ViewSet for managing Recipe APIs"""

    serializer_class = serializers.RecipeDetailsSerializer
    queryset = Recipe.objects.all()

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_int(self, qs):
        """Turns String representations into integers"""

        return [int(split_value) for split_value in qs.split(',')]

    def get_queryset(self):
        """Retrieves recipes for authenticated user"""

        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        queryset = self.queryset

        if tags:
            tag_ids = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Creates a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""

        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class RecipeAttributeViewSet(mixins.ListModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    """A ViewSet for managing Recipe different Attributes"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieves tags for authenticated user"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )

        queryset = self.queryset

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by('-name').distinct()


class TagViewSet(RecipeAttributeViewSet):
    """ A ViewSet for managing our tags"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(RecipeAttributeViewSet):
    """A ViewSet for managing Ingredients"""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
