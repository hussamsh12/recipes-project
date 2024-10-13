"""
Tests for Ingredients API
"""


from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')

def create_user(email='test@example.com', password='password123'):
    """Creates and returns a new user"""

    return get_user_model().objects.create_user(email=email, password=password)


def details_url(ingredient_id):
    """Create and return an ingredient details URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PublicRecipeAPITests(TestCase):
    """Tests unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()


    def test_authentication_required(self):
        """Tests that authentication is required to call API."""

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Tests for authenticated requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)


    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""

        Ingredient.objects.create(user=self.user, name='Carrot')
        Ingredient.objects.create(user=self.user, name="Eggplant")

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')

        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Tests list of ingredients is limited to authenticated user"""

        user2 = create_user('user2@example.com')

        Ingredient.objects.create(user=user2, name="Carrot")
        ingredient = Ingredient.objects.create(user=self.user, name="Eggplant")

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)


    def test_update_ingredient(self):
        """Tests updating an ingredient is successful"""

        ingredient = Ingredient.objects.create(user=self.user, name='Carror')

        payload = {
            'name': 'Eggplant'
        }

        url = details_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])



    def test_delete_ingredient(self):
        """Tests deleting an ingredient"""

        ingredient = Ingredient.objects.create(user=self.user, name='Carrot')

        url = details_url(ingredient.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)

        self.assertFalse(ingredients.exists())


    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredients to those assigned to recipe"""

        ing1 = Ingredient.objects.create(user=self.user, name='Oranges')
        ing2 = Ingredient.objects.create(user=self.user, name='Apples')

        recipe = Recipe.objects.create(
            title='Apple Pie',
            time_minutes=30,
            price='5.5',
            user=self.user
        )

        recipe.ingredients.add(ing2)
        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})


        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)

        self.assertIn(s2.data, res.data)
        self.assertNotIn(s1.data, res.data)


    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients return a unique value"""

        ing = Ingredient.objects.create(user=self.user, name='Eggs')

        Ingredient.objects.create(user=self.user, name='Chickpea')

        r1 = Recipe.objects.create(
            title='Scrambled Eggs',
            time_minutes=30,
            price='5.5',
            user=self.user
        )

        r2 = Recipe.objects.create(
            title='Boiled Eggs',
            time_minutes=30,
            price='5.5',
            user=self.user
        )

        r1.ingredients.add(ing)
        r2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
