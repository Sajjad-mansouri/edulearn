from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import Role
from profiles.models import InstructorProfile, Profile

User = get_user_model()


class UserRegisterationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class StudentRegistrationSerializer(UserRegisterationSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta(UserRegisterationSerializer.Meta):
        model = User
        fields = UserRegisterationSerializer.Meta.fields + ["password1", "password2"]

    def validate(self, attrs):
        password1 = attrs["password1"]
        password2 = attrs["password2"]

        if password1 != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        validate_password(password1)
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class CurrentUserSerializer(serializers.ModelSerializer):
    is_authenticated = serializers.SerializerMethodField()
    is_instructor = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "is_authenticated",
            "is_instructor",
            "is_student",
            "avatar",
            "first_name",
            "last_name",
        )

    def get_is_authenticated(self, obj):
        return True

    def get_is_instructor(self, obj):
        return obj.roles.filter(name=Role.Roles.INSTRUCTOR).exists()

    def get_is_student(self, obj):
        return obj.roles.filter(name=Role.Roles.STUDENT).exists()

    def get_avatar(self, obj):
        return obj.avatar


class UserRegisterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["website", "country", "linkedin", "github"]


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = [
            "headline",
            "biography",
            "professional_title",
            "organization",
            "years_of_experience",
        ]
