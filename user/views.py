"""
Views for the user API
"""

from rest_framework import generics

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """ Endpoint for creating a new user in our system"""
    serializer_class = UserSerializer



