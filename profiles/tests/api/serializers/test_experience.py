from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from profiles.api.serializers.experience import ExperienceSerializer
from profiles.models import Experience, Profile

User = get_user_model()


@pytest.fixture
def profile(db):
    user = User.objects.create_user(
        username="experience_test_user",
        email="experience_test_user@example.com",
        password="test-password",
    )
    return Profile.objects.create(user=user)


@pytest.fixture
def experience(db, profile):
    return Experience.objects.create(
        profile=profile,
        company="Example Technologies",
        position="Backend Developer",
        location="Baku",
        description="Developed and maintained backend services.",
        start_date=date(2020, 1, 15),
        end_date=date(2024, 6, 30),
        is_current=False,
    )


@pytest.fixture
def serializer():
    return ExperienceSerializer()


class TestExperienceSerializer:
    def test_contains_expected_fields(self, serializer):
        assert set(serializer.fields) == {
            "id",
            "company",
            "position",
            "location",
            "description",
            "start_date",
            "end_date",
        }

    def test_representation_contains_expected_values(self, experience):
        serializer = ExperienceSerializer(experience)

        assert serializer.data == {
            "id": experience.id,
            "company": "Example Technologies",
            "position": "Backend Developer",
            "location": "Baku",
            "description": "Developed and maintained backend services.",
            "start_date": "2020-01-15",
            "end_date": "2024-06-30",
        }

    def test_id_is_read_only(self, serializer):
        assert serializer.fields["id"].read_only is True

    @pytest.mark.parametrize(
        "field",
        [
            "company",
            "position",
            "location",
            "description",
            "start_date",
            "end_date",
        ],
    )
    def test_expected_fields_are_writable(self, serializer, field):
        assert serializer.fields[field].read_only is False

    def test_profile_is_not_exposed(self, serializer):
        assert "profile" not in serializer.fields

    def test_is_current_is_not_exposed(self, serializer):
        assert "is_current" not in serializer.fields

    def test_company_is_required(self, serializer):
        assert serializer.fields["company"].required is True

    def test_position_is_required(self, serializer):
        assert serializer.fields["position"].required is True

    def test_location_is_optional(self, serializer):
        assert serializer.fields["location"].required is False

    def test_description_is_optional(self, serializer):
        assert serializer.fields["description"].required is False

    def test_start_date_is_optional(self, serializer):
        assert serializer.fields["start_date"].required is False
        assert serializer.fields["start_date"].allow_null is True

    def test_end_date_is_optional(self, serializer):
        assert serializer.fields["end_date"].required is False
        assert serializer.fields["end_date"].allow_null is True

    def test_valid_complete_input(self, profile):
        data = {
            "company": "Example Technologies",
            "position": "Senior Backend Developer",
            "location": "Baku",
            "description": "Designed and implemented scalable backend services.",
            "start_date": "2020-01-15",
            "end_date": "2024-06-30",
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {
            "company": "Example Technologies",
            "position": "Senior Backend Developer",
            "location": "Baku",
            "description": "Designed and implemented scalable backend services.",
            "start_date": date(2020, 1, 15),
            "end_date": date(2024, 6, 30),
        }

    def test_optional_fields_can_be_omitted(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["company"] == "Example Technologies"
        assert serializer.validated_data["position"] == "Backend Developer"
        assert "location" not in serializer.validated_data
        assert "description" not in serializer.validated_data
        assert "start_date" not in serializer.validated_data
        assert "end_date" not in serializer.validated_data

    def test_optional_text_fields_accept_empty_strings(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            "location": "",
            "description": "",
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["location"] == ""
        assert serializer.validated_data["description"] == ""

    def test_nullable_dates_accept_null(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            "start_date": None,
            "end_date": None,
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["start_date"] is None
        assert serializer.validated_data["end_date"] is None

    def test_current_position_can_be_serialized_without_end_date(self, profile):
        experience = Experience.objects.create(
            profile=profile,
            company="Current Company",
            position="Backend Developer",
            location="Baku",
            description="Current position.",
            start_date=date(2024, 1, 1),
            end_date=None,
            is_current=True,
        )

        serializer = ExperienceSerializer(experience)

        assert serializer.data["company"] == "Current Company"
        assert serializer.data["position"] == "Backend Developer"
        assert serializer.data["start_date"] == "2024-01-01"
        assert serializer.data["end_date"] is None

    def test_date_strings_are_coerced_to_date_objects(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            "start_date": "2021-03-10",
            "end_date": "2023-08-20",
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["start_date"] == date(2021, 3, 10)
        assert serializer.validated_data["end_date"] == date(2023, 8, 20)

    @pytest.mark.parametrize(
        "field",
        ["start_date", "end_date"],
    )
    @pytest.mark.parametrize(
        "value",
        [
            "",
            "2024/01/01",
            "01-01-2024",
            "not-a-date",
            "2024-13-01",
            "2024-02-30",
        ],
    )
    def test_invalid_date_values_are_rejected(self, field, value):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            field: value,
        }

        serializer = ExperienceSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_missing_company_is_rejected(self):
        data = {
            "position": "Backend Developer",
        }

        serializer = ExperienceSerializer(data=data)

        assert not serializer.is_valid()
        assert "company" in serializer.errors

    def test_missing_position_is_rejected(self):
        data = {
            "company": "Example Technologies",
        }

        serializer = ExperienceSerializer(data=data)

        assert not serializer.is_valid()
        assert "position" in serializer.errors

    def test_empty_company_is_rejected(self):
        data = {
            "company": "",
            "position": "Backend Developer",
        }

        serializer = ExperienceSerializer(data=data)

        assert not serializer.is_valid()
        assert "company" in serializer.errors

    def test_empty_position_is_rejected(self):
        data = {
            "company": "Example Technologies",
            "position": "",
        }

        serializer = ExperienceSerializer(data=data)

        assert not serializer.is_valid()
        assert "position" in serializer.errors

    def test_company_accepts_maximum_length(self):
        company = "C" * 255

        serializer = ExperienceSerializer(
            data={
                "company": company,
                "position": "Backend Developer",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["company"] == company

    def test_company_rejects_value_longer_than_maximum_length(self):
        serializer = ExperienceSerializer(
            data={
                "company": "C" * 256,
                "position": "Backend Developer",
            }
        )

        assert not serializer.is_valid()
        assert "company" in serializer.errors

    def test_position_accepts_maximum_length(self):
        position = "P" * 255

        serializer = ExperienceSerializer(
            data={
                "company": "Example Technologies",
                "position": position,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["position"] == position

    def test_position_rejects_value_longer_than_maximum_length(self):
        serializer = ExperienceSerializer(
            data={
                "company": "Example Technologies",
                "position": "P" * 256,
            }
        )

        assert not serializer.is_valid()
        assert "position" in serializer.errors

    def test_location_accepts_maximum_length(self):
        location = "L" * 250

        serializer = ExperienceSerializer(
            data={
                "company": "Example Technologies",
                "position": "Backend Developer",
                "location": location,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["location"] == location

    def test_location_rejects_value_longer_than_maximum_length(self):
        serializer = ExperienceSerializer(
            data={
                "company": "Example Technologies",
                "position": "Backend Developer",
                "location": "L" * 251,
            }
        )

        assert not serializer.is_valid()
        assert "location" in serializer.errors

    def test_description_accepts_long_text(self):
        description = "D" * 5000

        serializer = ExperienceSerializer(
            data={
                "company": "Example Technologies",
                "position": "Backend Developer",
                "description": description,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == description

    def test_input_id_is_ignored(self, experience):
        original_id = str(experience.id)

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "company": "Updated Company",
            "position": "Updated Position",
        }

        serializer = ExperienceSerializer(
            instance=experience,
            data=data,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

        updated_experience = serializer.save()

        assert str(updated_experience.id) == original_id

    def test_profile_is_not_changed_by_serializer_update(self, experience, profile):
        original_profile_id = experience.profile_id

        serializer = ExperienceSerializer(
            instance=experience,
            data={
                "company": "Updated Company",
                "position": "Updated Position",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        updated_experience = serializer.save()

        assert updated_experience.profile_id == original_profile_id
        assert updated_experience.profile_id == profile.id

    def test_unknown_input_fields_are_ignored(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            "unknown_field": "unexpected value",
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert "unknown_field" not in serializer.validated_data

    def test_is_current_input_is_ignored(self):
        data = {
            "company": "Example Technologies",
            "position": "Backend Developer",
            "is_current": True,
        }

        serializer = ExperienceSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert "is_current" not in serializer.validated_data

    def test_partial_update(self, experience):
        serializer = ExperienceSerializer(
            instance=experience,
            data={"position": "Senior Backend Developer"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_experience = serializer.save()

        assert updated_experience.position == "Senior Backend Developer"
        assert updated_experience.company == "Example Technologies"
        assert updated_experience.location == "Baku"
        assert updated_experience.description == (
            "Developed and maintained backend services."
        )

    def test_partial_update_can_set_nullable_dates_to_none(self, experience):
        serializer = ExperienceSerializer(
            instance=experience,
            data={
                "start_date": None,
                "end_date": None,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_experience = serializer.save()

        assert updated_experience.start_date is None
        assert updated_experience.end_date is None

    def test_full_update_requires_required_fields(self, experience):
        serializer = ExperienceSerializer(
            instance=experience,
            data={
                "company": "Updated Company",
            },
        )

        assert not serializer.is_valid()
        assert "position" in serializer.errors

    def test_full_update_can_omit_optional_fields(self, experience):
        serializer = ExperienceSerializer(
            instance=experience,
            data={
                "company": "Updated Company",
                "position": "Senior Developer",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_experience = serializer.save()

        assert updated_experience.company == "Updated Company"
        assert updated_experience.position == "Senior Developer"

    def test_serialization_does_not_mutate_instance(self, experience):
        original_values = {
            "company": experience.company,
            "position": experience.position,
            "location": experience.location,
            "description": experience.description,
            "start_date": experience.start_date,
            "end_date": experience.end_date,
            "is_current": experience.is_current,
            "profile_id": experience.profile_id,
        }

        serializer = ExperienceSerializer(experience)

        _ = serializer.data

        experience.refresh_from_db()

        assert experience.company == original_values["company"]
        assert experience.position == original_values["position"]
        assert experience.location == original_values["location"]
        assert experience.description == original_values["description"]
        assert experience.start_date == original_values["start_date"]
        assert experience.end_date == original_values["end_date"]
        assert experience.is_current == original_values["is_current"]
        assert experience.profile_id == original_values["profile_id"]

    def test_invalid_data_raises_validation_error_when_accessing_validated_data(self):
        serializer = ExperienceSerializer(
            data={
                "company": "",
                "position": "",
            }
        )

        with pytest.raises(ValidationError):
            _ = serializer.is_valid(raise_exception=True)
