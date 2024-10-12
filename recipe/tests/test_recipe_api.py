"""
Tests for recipe API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailsSerializer


RECIPES_URL = reverse("recipe:recipe-list")

def details_url(recipe_id):
    """Create and return a recipe details URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe"""

    defaults = {
        'title': 'Sample Title',
        'time_minutes': 10,
        'price': Decimal("3.5"),
        'description': "Sample Recipe Description",
        'link': 'http://example.com/recipe.txt'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeAPITests(TestCase):
    """Tests unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()


    def test_authentication_required(self):
        """Tests that authentication is required to call API."""

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Tests authenticated API requests."""

    def setUp(self):

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)


    def test_retrieve_recipes(self):
        """Tests retrieving a list of recipes is correct"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authorized user"""

        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            password='password123'
        )

        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_details(self):
        """Test get recipe details successful"""

        recipe = create_recipe(user=self.user)

        url = details_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailsSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)



    def test_create_recipe(self):
        """Tests Creating a recipe"""

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': Decimal('5.99')
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""

        payload = {
            'title': 'Curry',
            'time_minutes': 30,
            'price': Decimal('2.5'),
            'tags': [
                {'name': 'Thai'},
                {'name': 'Dinner'}
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tags."""
        tag_arab_food = Tag.objects.create(user=self.user, name='Arab Food')

        payload = {
            'title': 'Upsidedown',
            'time_minutes': 30,
            'price': Decimal('50'),
            'tags': [
                {'name': 'Arab Food'},
                {'name': 'Lunch'}
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_arab_food, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name']
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        """Tests creating a tag when updating a recipe"""

        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Dinner'}]}

        url = details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='Dinner')

        self.assertIn(new_tag, recipe.tags.all())


    def test_update_recipe_assign_tag(self):
        """Assigning an existing tag when updating"""

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')

        recipe = create_recipe(user=self.user)
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        recipe.tags.add(tag_breakfast)

        payload = {
            'tags': [{'name': 'Lunch'}]
        }

        url = details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clearing_a_recipe_tags(self):
        """Tests clearing a recipe tags"""

        tag = Tag.objects.create(user=self.user, name='Lunch')
        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag)

        payload ={'tags': []}
        url = details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)


