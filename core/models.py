"""
Models for our system
"""

import uuid
import os

from django.db import models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from recipes_api import settings


def recipe_image_file_path(instance, filename):
    """Generates file path for new recipe image"""

    extension = os.path.splitext(filename)[1]
    filename = "{}{}".format(uuid.uuid4(), extension)
    return os.path.join('uploads', 'recipe', filename)



class UserManager(BaseUserManager):
    """ Manager for the Users in the system"""

    def create_user(self, email, password=None, **extra_field):
        """Creates a user in the system"""
        if not email:
            raise ValueError("Must provide an email")
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_field)
        user.set_password(password)
        user.save(using=self._db)

        return user


    def create_superuser(self, email, password=None):
        """Creates a superuser"""
        user = self.create_user(email, password)

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user



class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'



class Recipe(models.Model):
    """The recipe model"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient')
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)


    def __str__(self):
        """String representation of the Recipe model"""
        return self.title


class Tag(models.Model):
    """The tag model"""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):

        """String representation of a tag"""
        return self.name


class Ingredient(models.Model):
    """Ingredients for our recipes"""

    name = models.CharField(max_length=255)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        """String representation of the ingredient model"""

        return self.name