import pytest
from django.db import IntegrityError

from accounts.models import User

from .factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_default_email_verified(self):
        user = UserFactory()

        assert user.email_verified is False

    def test_email_unique(self):
        UserFactory(email="john@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="john@example.com")

    def test_required_fields(self):
        assert User.REQUIRED_FIELDS == ["email"]

    def test_username_index_exists(self):
        index = User._meta.indexes[0]

        assert index.fields == ["username"]
