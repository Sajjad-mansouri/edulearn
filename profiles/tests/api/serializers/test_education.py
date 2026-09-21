from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from profiles.api.serializers.education import EducationSerializer
from profiles.models import Education, Profile

User = get_user_model()


@pytest.fixture
def profile(db):
    user = User.objects.create_user(
        username="education_test_user",
        email="education_test_user@example.com",
        password="test-password",
    )

    return Profile.objects.create(user=user)


@pytest.fixture
def education(db, profile):
    return Education.objects.create(
        profile=profile,
        institution="University of Example",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
        description="Studied software engineering and computer science.",
        start_date=date(2018, 9, 1),
        end_date=date(2022, 6, 30),
    )


@pytest.mark.django_db
class TestEducationSerializer:
    def test_serializes_expected_fields(self, education):
        serializer = EducationSerializer(education)

        assert set(serializer.data.keys()) == {
            "id",
            "institution",
            "degree",
            "field_of_study",
            "description",
            "start_date",
            "end_date",
        }

    def test_serializes_education_instance(self, education):
        serializer = EducationSerializer(education)

        assert serializer.data == {
            "id": education.id,
            "institution": "University of Example",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "description": ("Studied software engineering and computer science."),
            "start_date": "2018-09-01",
            "end_date": "2022-06-30",
        }

    def test_serializes_id_as_integer(self, education):
        serializer = EducationSerializer(education)

        assert serializer.data["id"] == education.id

    def test_id_is_read_only(self):
        serializer = EducationSerializer()

        assert serializer.fields["id"].read_only is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "institution",
            "degree",
            "field_of_study",
            "description",
            "start_date",
            "end_date",
        ],
    )
    def test_non_id_fields_are_not_read_only(self, field_name):
        serializer = EducationSerializer()

        assert serializer.fields[field_name].read_only is False

    def test_institution_is_required(self):
        serializer = EducationSerializer(
            data={
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
            }
        )

        assert not serializer.is_valid()

        assert "institution" in serializer.errors

    def test_degree_is_required(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "field_of_study": "Computer Science",
            }
        )

        assert not serializer.is_valid()

        assert "degree" in serializer.errors

    def test_field_of_study_is_required(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
            }
        )

        assert not serializer.is_valid()

        assert "field_of_study" in serializer.errors

    def test_description_is_optional(self):
        serializer = EducationSerializer()

        assert serializer.fields["description"].required is False

    def test_start_date_is_optional(self):
        serializer = EducationSerializer()

        assert serializer.fields["start_date"].required is False
        assert serializer.fields["start_date"].allow_null is True

    def test_end_date_is_optional(self):
        serializer = EducationSerializer()

        assert serializer.fields["end_date"].required is False
        assert serializer.fields["end_date"].allow_null is True

    def test_accepts_complete_valid_input(self):
        data = {
            "institution": "University of Example",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "description": "Studied software engineering.",
            "start_date": "2018-09-01",
            "end_date": "2022-06-30",
        }

        serializer = EducationSerializer(data=data)

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "institution": "University of Example",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "description": "Studied software engineering.",
            "start_date": date(2018, 9, 1),
            "end_date": date(2022, 6, 30),
        }

    def test_converts_date_strings_to_date_objects(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "2018-09-01",
                "end_date": "2022-06-30",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["start_date"] == date(2018, 9, 1)
        assert serializer.validated_data["end_date"] == date(2022, 6, 30)

    def test_accepts_null_start_date(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": None,
                "end_date": None,
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["start_date"] is None
        assert serializer.validated_data["end_date"] is None

    def test_accepts_null_end_date_for_current_education(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Master of Science",
                "field_of_study": "Computer Science",
                "start_date": "2023-09-01",
                "end_date": None,
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["start_date"] == date(2023, 9, 1)
        assert serializer.validated_data["end_date"] is None

    def test_accepts_same_start_and_end_date(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "2022-06-30",
                "end_date": "2022-06-30",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["start_date"] == date(2022, 6, 30)
        assert serializer.validated_data["end_date"] == date(2022, 6, 30)

    def test_serializer_does_not_expose_profile(self, education):
        serializer = EducationSerializer(education)

        assert "profile" not in serializer.data
        assert "profile" not in serializer.fields

    def test_serializer_does_not_expose_unlisted_model_fields(
        self,
        education,
    ):
        serializer = EducationSerializer(education)

        assert set(serializer.data.keys()).isdisjoint(
            {
                "profile",
            }
        )

    def test_rejects_invalid_start_date_format(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "not-a-date",
            }
        )

        assert not serializer.is_valid()

        assert "start_date" in serializer.errors

    def test_rejects_invalid_end_date_format(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "end_date": "not-a-date",
            }
        )

        assert not serializer.is_valid()

        assert "end_date" in serializer.errors

    @pytest.mark.parametrize(
        "date_value",
        [
            "2024-13-01",
            "2024-00-01",
            "2024-01-32",
            "01-01-2024",
        ],
    )
    def test_rejects_invalid_start_date_values(self, date_value):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": date_value,
            }
        )

        assert not serializer.is_valid()

        assert "start_date" in serializer.errors

    @pytest.mark.parametrize(
        "date_value",
        [
            "2024-13-01",
            "2024-00-01",
            "2024-01-32",
            "01-01-2024",
        ],
    )
    def test_rejects_invalid_end_date_values(self, date_value):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "end_date": date_value,
            }
        )

        assert not serializer.is_valid()

        assert "end_date" in serializer.errors

    def test_rejects_institution_longer_than_255_characters(self):
        serializer = EducationSerializer(
            data={
                "institution": "I" * 256,
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
            }
        )

        assert not serializer.is_valid()

        assert "institution" in serializer.errors

    def test_rejects_degree_longer_than_255_characters(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "D" * 256,
                "field_of_study": "Computer Science",
            }
        )

        assert not serializer.is_valid()

        assert "degree" in serializer.errors

    def test_rejects_field_of_study_longer_than_255_characters(self):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": "F" * 256,
            }
        )

        assert not serializer.is_valid()

        assert "field_of_study" in serializer.errors

    def test_accepts_maximum_institution_length(self):
        institution = "I" * 255

        serializer = EducationSerializer(
            data={
                "institution": institution,
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["institution"] == institution

    def test_accepts_maximum_degree_length(self):
        degree = "D" * 255

        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": degree,
                "field_of_study": "Computer Science",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["degree"] == degree

    def test_accepts_maximum_field_of_study_length(self):
        field_of_study = "F" * 255

        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "degree": "Bachelor of Science",
                "field_of_study": field_of_study,
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["field_of_study"] == field_of_study

    def test_all_expected_fields_are_present_in_serializer(self):
        serializer = EducationSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "institution",
            "degree",
            "field_of_study",
            "description",
            "start_date",
            "end_date",
        }

    def test_serializer_is_not_read_only(self):
        serializer = EducationSerializer()

        assert serializer.read_only is False

    def test_partial_update_only_changes_supplied_fields(
        self,
        education,
    ):
        serializer = EducationSerializer(
            education,
            data={
                "degree": "Master of Science",
            },
            partial=True,
        )

        assert serializer.is_valid()

        updated_education = serializer.save()

        assert updated_education.degree == "Master of Science"
        assert updated_education.institution == "University of Example"
        assert updated_education.field_of_study == "Computer Science"
        assert (
            updated_education.description
            == "Studied software engineering and computer science."
        )
        assert updated_education.start_date == date(2018, 9, 1)
        assert updated_education.end_date == date(2022, 6, 30)

    def test_update_changes_all_writable_fields(
        self,
        education,
    ):
        serializer = EducationSerializer(
            education,
            data={
                "institution": "Another University",
                "degree": "Master of Science",
                "field_of_study": "Data Science",
                "description": "Graduate studies in data science.",
                "start_date": "2023-09-01",
                "end_date": "2025-06-30",
            },
        )

        assert serializer.is_valid()

        updated_education = serializer.save()

        assert updated_education.institution == "Another University"
        assert updated_education.degree == "Master of Science"
        assert updated_education.field_of_study == "Data Science"
        assert updated_education.description == ("Graduate studies in data science.")
        assert updated_education.start_date == date(2023, 9, 1)
        assert updated_education.end_date == date(2025, 6, 30)

    def test_update_does_not_change_profile(
        self,
        education,
        profile,
    ):
        original_profile_id = education.profile_id

        serializer = EducationSerializer(
            education,
            data={
                "institution": "Another University",
                "degree": education.degree,
                "field_of_study": education.field_of_study,
            },
            partial=True,
        )

        assert serializer.is_valid()

        updated_education = serializer.save()

        assert updated_education.profile_id == original_profile_id
        assert updated_education.profile_id == profile.id

    def test_input_id_cannot_change_existing_education_id(
        self,
        education,
    ):
        original_id = education.id

        serializer = EducationSerializer(
            education,
            data={
                "id": 999999,
                "institution": education.institution,
                "degree": education.degree,
                "field_of_study": education.field_of_study,
            },
        )

        assert serializer.is_valid()

        assert serializer.validated_data.get("id") is None

        updated_education = serializer.save()

        assert updated_education.id == original_id

    def test_unknown_input_field_is_ignored(
        self,
        education,
    ):
        serializer = EducationSerializer(
            education,
            data={
                "institution": "Another University",
                "unexpected_field": "unexpected value",
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "unexpected_field" not in serializer.validated_data

    def test_serialization_does_not_modify_instance(
        self,
        education,
    ):
        original_values = {
            "id": education.id,
            "institution": education.institution,
            "degree": education.degree,
            "field_of_study": education.field_of_study,
            "description": education.description,
            "start_date": education.start_date,
            "end_date": education.end_date,
            "profile_id": education.profile_id,
        }

        serializer = EducationSerializer(education)

        _ = serializer.data

        assert education.id == original_values["id"]
        assert education.institution == original_values["institution"]
        assert education.degree == original_values["degree"]
        assert education.field_of_study == original_values["field_of_study"]
        assert education.description == original_values["description"]
        assert education.start_date == original_values["start_date"]
        assert education.end_date == original_values["end_date"]
        assert education.profile_id == original_values["profile_id"]

    def test_invalid_data_raises_validation_error_when_requested(
        self,
    ):
        serializer = EducationSerializer(
            data={
                "institution": "University of Example",
                "field_of_study": "Computer Science",
                "start_date": "not-a-date",
            }
        )

        with pytest.raises(ValidationError):
            _ = serializer.is_valid(raise_exception=True)
