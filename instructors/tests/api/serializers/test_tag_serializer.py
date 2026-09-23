from rest_framework import serializers

from courses.models import Tag
from instructors.api.serializers.tag import TagSerializer


class TestTagSerializer:
    def test_serializer_has_expected_fields(self):
        serializer = TagSerializer()

        assert list(serializer.fields) == ["id", "name"]

    def test_id_is_read_only(self):
        serializer = TagSerializer()

        assert serializer.fields["id"].read_only is True

    def test_name_is_required(self):
        serializer = TagSerializer()

        assert serializer.fields["name"].required is True
        assert serializer.fields["name"].allow_blank is False

    def test_name_uses_char_field(self):
        serializer = TagSerializer()

        assert isinstance(serializer.fields["name"], serializers.CharField)

    def test_name_has_expected_max_length(self):
        serializer = TagSerializer()

        assert serializer.fields["name"].max_length == 100

    def test_valid_data_is_accepted(self):
        serializer = TagSerializer(data={"name": "Django"})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {"name": "Django"}

    def test_name_is_required_in_input(self):
        serializer = TagSerializer(data={})

        assert not serializer.is_valid()
        assert serializer.errors["name"][0].code == "required"

    def test_blank_name_is_rejected(self):
        serializer = TagSerializer(data={"name": ""})

        assert not serializer.is_valid()
        assert serializer.errors["name"][0].code == "blank"

    def test_name_longer_than_100_characters_is_rejected(self):
        serializer = TagSerializer(data={"name": "a" * 101})

        assert not serializer.is_valid()
        assert serializer.errors["name"][0].code == "max_length"

    def test_name_with_exactly_100_characters_is_accepted(self):
        name = "a" * 100
        serializer = TagSerializer(data={"name": name})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["name"] == name

    def test_id_is_ignored_when_provided_as_input(self):
        serializer = TagSerializer(
            data={
                "id": 123,
                "name": "Django",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {"name": "Django"}

    def test_serializes_tag_instance(self, db):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        serializer = TagSerializer(instance=tag)

        assert serializer.data == {
            "id": tag.id,
            "name": "Django",
        }

    def test_serializes_name_exactly_as_stored(self, db):
        tag = Tag.objects.create(
            name="Django REST Framework",
            slug="django-rest-framework",
        )

        serializer = TagSerializer(instance=tag)

        assert serializer.data["name"] == "Django REST Framework"

    def test_serializer_save_creates_tag(self, db):
        serializer = TagSerializer(data={"name": "Django"})

        assert serializer.is_valid(), serializer.errors

        tag = serializer.save()

        assert isinstance(tag, Tag)
        assert tag.name == "Django"
        assert tag.slug == "django"

    def test_serializer_save_generates_slug_from_name(self, db):
        serializer = TagSerializer(data={"name": "Django REST Framework"})

        assert serializer.is_valid(), serializer.errors

        tag = serializer.save()

        assert tag.slug == "django-rest-framework"

    def test_serializer_save_persists_tag(self, db):
        serializer = TagSerializer(data={"name": "Python"})

        assert serializer.is_valid(), serializer.errors

        tag = serializer.save()

        assert Tag.objects.filter(pk=tag.pk).exists()

    def test_update_tag_name(self, db):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        serializer = TagSerializer(
            instance=tag,
            data={"name": "Django REST Framework"},
        )

        assert serializer.is_valid(), serializer.errors

        updated_tag = serializer.save()

        assert updated_tag.pk == tag.pk
        assert updated_tag.name == "Django REST Framework"

    def test_update_does_not_expose_slug(self, db):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        serializer = TagSerializer(
            instance=tag,
            data={
                "name": "Django REST Framework",
                "slug": "custom-slug",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_tag = serializer.save()

        assert updated_tag.slug == "django"
