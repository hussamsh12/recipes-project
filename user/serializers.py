"""
Serializers for the User API
"""


from django.contrib.auth import get_user_model, authenticate

from rest_framework import serializers,


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user model"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            }
        }

    def create(self, validated_data):
        """ Creates and returns a new user with encrypted password"""

        return get_user_model().objects.create_user(**validated_data)



class AuthTokenSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(
        style= {'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the credentials and the user"""

        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            username=email,
            password=password
        )

        if not user:
            msg = 'Unable to Authenticate User with Provided Credentials'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs