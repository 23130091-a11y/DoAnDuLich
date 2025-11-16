from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer) :
    class Meta:
        model = User
        fields = ['id', 'email', 'password']

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user