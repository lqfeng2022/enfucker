from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer
)
from .models import Profile


# Custom serializer (add 'first_name', 'last_name')
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']


class UserSimpleSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    # Add nested user fields
    username = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'birth_date', 'bro', 'description']
        read_only_fields = ['bro']

    def validate_email(self, value):
        user = self.instance.user  # current logged-in user
        User = user.__class__      # get the User model class

        # `exclude()`: excluding the current user when the user keeps their current email
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def update(self, instance, validated_data):
        # pop `user` out then put into an empty dict
        user_data = validated_data.pop('user', {})
        user = instance.user  # `instance`: the current model object

        # update the User fields
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # update the Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
