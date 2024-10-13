"""
Tests for recipe API
"""
from decimal import Decimal
import tempfile
import os
from PIL import Image


from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailsSerializer


RECIPES_URL = reverse("recipe:recipe-list")

def details_url(recipe_id):
    """Create and return a recipe details URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create abd return image URL for recipe"""

    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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



    def check_ingredients(self, payload, recipe):
        """Check if the ingredients in the payload are present in the recipe"""

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name']
            ).exists()

            self.assertTrue(exists)


    def test_create_recipe_with_new_ingredient(self):
        """Tests creating a recipe with new ingredient"""

        payload = {
            'title': 'Pasta',
            'time_minutes': 50,
            'price': '3.5',
            'ingredients': [{'name': 'Flour'}, {'name': "Eggs"}, {'name': 'Salt'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        self.check_ingredients(payload, recipe)


    def test_create_recipe_with_existing_ingredient(self):
        """Tests creating a recipe with existing ingredients"""

        ingredient = Ingredient.objects.create(user=self.user, name='Limes')

        payload = {
            'title': 'Lemonade',
            'time_minutes': 5,
            'price': 10,
            'ingredients': [{'name': 'Limes'}, {'name': 'Sugar'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        self.check_ingredients(payload, recipe)



    def test_create_ingredient_on_update(self):
        """tests creating an ingredient on update"""

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': "Limes"}]}

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(name='Limes', user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assigns_ingredients(self):
        """Test updating a recipe assigns an ingredient"""

        in1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(in1)
        in2 = Ingredient.objects.create(user=self.user, name='Chili')

        payload = {'ingredients': [{'name': 'Chili'}]}

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(in2, recipe.ingredients.all())
        self.assertNotIn(in1, recipe.ingredients.all())


    def test_clear_recipe_ingredients(self):
        """Tests clearing recipe Ingredients"""

        ing = Ingredient.objects.create(user=self.user, name='Pepper')

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing)

        payload = {'ingredients': []}

        url = details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""

        r1 = create_recipe(user=self.user, title='Thai Vegetable Curry ')
        r2 = create_recipe(user=self.user, title='Baba Ghanoj')

        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')

        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_recipe(user=self.user, title='Schnetizel')

        params = {'tags': '{},{}'.format(tag1.id, tag2.id)}

        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


    def test_filter_by_ingredient(self):
        r1 = create_recipe(user=self.user, title='Thai Vegetable Curry ')
        r2 = create_recipe(user=self.user, title='Baba Ghanoj')

        ing1 = Ingredient.objects.create(user=self.user, name='Onions')
        ing2 = Ingredient.objects.create(user=self.user, name='Eggplant')

        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        r3 = create_recipe(user=self.user, title='Fish and Chips')

        params = {'ingredients': '{},{}'.format(ing1.id, ing2.id)}

        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)




class ImageUploadTest(TestCase):


    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user@example.com', 'password')
        self.recipe = create_recipe(user=self.user)
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))


    def test_upload_image_bad_request(self):
        """Test uploading incalid images"""

        url = image_upload_url(self.recipe.id)

        payload = {'image': 'Not an Image'}

        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)





