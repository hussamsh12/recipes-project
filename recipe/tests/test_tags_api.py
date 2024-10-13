"""
Tests for the tags API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer
from recipe.tests.test_recipe_api import RECIPES_URL

TAGS_URL = reverse('recipe:tag-list')

def details_url(tag_id):
    """Create and return a tag details url"""

    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email='test@example.com', password='password123'):
    """Creates and returns a new user"""

    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
    """Tests for unauthenticated requests"""

    def setUp(self):
        self.client = APIClient()


    def test_auth_is_required(self):
        """Test Auth is required for retrieving tags"""

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Tests authenticated requests."""


    def setUp(self):
        self.user = create_user()
        self.client = APIClient()

        self.client.force_authenticate(user=self.user)


    def test_retrieve_tags(self):
        """Tests retrieving tags is successful for authenticated user"""

        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Tests list of tags is limited to authenticated user"""

        user2 = create_user('user2@example.com')

        Tag.objects.create(user=user2, name="Vegan")
        tag = Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)


    def test_update_tag(self):
        """Tests updating a tag"""
        tag = Tag.objects.create(user=self.user, name='Lunch')

        payload ={
            'name': 'Breakfast'
        }

        url = details_url(tag.id)

        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(tag.name, payload['name'])


    def test_delete_tag(self):
        """Tests deleting a tag"""

        tag = Tag.objects.create(user=self.user, name='Lunch')

        url = details_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)

        self.assertFalse(tags.exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredients to those assigned to recipe"""

        t1 = Tag.objects.create(user=self.user, name='Vegan')
        t2 = Tag.objects.create(user=self.user, name='Vegetarian')

        recipe = Recipe.objects.create(
            title='Apple Pie',
            user=self.user,
            time_minutes=30,
            price='5.5',
        )

        recipe.tags.add(t2)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(t1)
        s2 = TagSerializer(t2)

        self.assertIn(s2.data, res.data)
        self.assertNotIn(s1.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients return a unique value"""

        tag = Tag.objects.create(user=self.user, name='Sour')

        Tag.objects.create(user=self.user, name='Chickpea')

        r1 = Recipe.objects.create(
            title='Scrambled Eggs',
            user=self.user,
            time_minutes=30,
            price='5.5',
        )

        r2 = Recipe.objects.create(
            title='Boiled Eggs',
            user=self.user,
            time_minutes=30,
            price='5.5',
        )

        r1.tags.add(tag)
        r2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)