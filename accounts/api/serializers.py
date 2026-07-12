from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    new_user_flag = True

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2",
        ]

    def validate(self, attrs):
        password1 = attrs["password1"]
        password2 = attrs["password2"]

        if password1 != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        validate_password(password1)
        return attrs
