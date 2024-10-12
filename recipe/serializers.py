"""
Serializers for recipe API
"""

from rest_framework import serializers

from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tag object"""

    class Meta:
        model = Tag
        fields = ('id', 'name',)

        read_only_fields = ('id',)



class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the Ingredients"""

    class Meta:
        model = Tag
        fields = ('id', 'name',)

        read_only_fields = ('id',)

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'title', 'time_minutes', 'price', 'link', 'tags')
        read_only_fields = ('id',)

    def _get_or_create_tags(self, tags, instance):
        """Gets or Creates Tags if it exists or not"""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, c = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            instance.tags.add(tag_obj)



    def create(self, validated_data):
        """Creates a recipe"""

        tags = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Updates a recipe"""

        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class RecipeDetailsSerializer(RecipeSerializer):
    """Serializer for the recipe details view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description', )