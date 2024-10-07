
"""
Tests for our models
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

class ModelTests(TestCase):
    """Test class for our application model"""

    def test_create_user_email_successful(self):
        """Testing creating a new user with email is successful"""

        email = "test@example.com"
        password= "password123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))


    def test_new_user_email_normalized(self):
        """Checks if the email is normalized or not"""

        sample_test = [
            ['test1@Example.com', 'test1@example.com'],
            ['Test2@example.Com', 'Test2@example.com'],
            ['test3@example.com', 'test3@example.com'],
        ]

        for email, expected in sample_test:
            user = get_user_model().objects.create_user(email, 'password123')
            self.assertEqual(user.email, expected)


    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises an error"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'password123')



    def test_create_superuser(self):
        """Tests Creating a superuser is successful"""


        user = get_user_model().objects.create_superuser(
            'test@exmaple.com',
            "pass123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


    def test_create_recipe(self):
        """Tests creating a recipe is successful"""

        user = get_user_model().objects.create_user(
            email='template@example.com',
            password='password123'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe title',
            time_minutes=10,
            price=Decimal("5.50"),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)


