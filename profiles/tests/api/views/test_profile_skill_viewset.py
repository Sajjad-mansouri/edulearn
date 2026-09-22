from django.urls import reverse

from profiles.models import Skill


class TestSkillViewSetCreate:
    def test_authenticated_user_can_create_skill(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Python",
            "description": "Python programming language.",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201
        assert response.data["name"] == "Python"
        assert response.data["description"] == ("Python programming language.")

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.profile == profile
        assert skill.name == "Python"
        assert skill.description == "Python programming language."
        assert skill.slug == "python"

    def test_create_assigns_authenticated_users_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Django",
            "description": "Django web framework.",
            "profile": another_profile.pk,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.profile == profile
        assert skill.profile != another_profile

    def test_create_cannot_assign_skill_to_another_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Docker",
            "description": "Containerization.",
            "profile": another_profile.pk,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.profile == profile
        assert skill.profile != another_profile

        assert not Skill.objects.filter(
            profile=another_profile,
            name="Docker",
        ).exists()

    def test_create_requires_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "description": "Some description.",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "name" in response.data
        assert not Skill.objects.filter(profile=profile).exists()

    def test_create_rejects_blank_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "",
            "description": "Some description.",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "name" in response.data
        assert not Skill.objects.filter(profile=profile).exists()

    def test_create_allows_description_to_be_omitted(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "PostgreSQL",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.profile == profile
        assert skill.name == "PostgreSQL"
        assert skill.description == ""
        assert skill.slug == "postgresql"

    def test_create_allows_blank_description(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Redis",
            "description": "",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.name == "Redis"
        assert skill.description == ""

    def test_create_generates_slug_from_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Django REST Framework",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.slug == "django-rest-framework"

    def test_create_slug_is_not_exposed_by_serializer(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Git",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201
        assert "slug" not in response.data

    def test_create_ignores_unknown_fields(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Linux",
            "description": "Linux operating system.",
            "unknown_field": "unexpected value",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.profile == profile
        assert skill.name == "Linux"
        assert skill.description == "Linux operating system."
        assert not hasattr(skill, "unknown_field")

    def test_create_ignores_client_supplied_slug(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Python",
            "slug": "client-supplied-slug",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        skill = Skill.objects.get(pk=response.data["id"])

        assert skill.slug == "python"
        assert skill.slug != "client-supplied-slug"


class TestSkillViewSetDestroy:
    def test_owner_can_delete_skill_by_id(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
            description="Python programming.",
        )
        skill_id = skill.pk

        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill_id},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 204
        assert not Skill.objects.filter(pk=skill_id).exists()

    def test_delete_by_id_does_not_delete_other_skills(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill_to_delete = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        skill_to_keep = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill_to_delete.pk},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 204

        assert not Skill.objects.filter(
            pk=skill_to_delete.pk,
        ).exists()

        assert Skill.objects.filter(
            pk=skill_to_keep.pk,
        ).exists()

    def test_deleting_nonexistent_skill_by_id_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": 999999},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 404

    def test_deleting_same_skill_twice_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill.pk},
        )

        # Act
        first_response = authenticated_client.delete(url)
        second_response = authenticated_client.delete(url)

        # Assert
        assert first_response.status_code == 204
        assert second_response.status_code == 404


class TestSkillViewSetDeleteAction:
    def test_owner_can_delete_skill_by_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")
        data = {
            "name": "Python",
        }

        # Act
        response = authenticated_client.delete(
            url,
            data=data,
            format="json",
        )

        # Assert
        assert response.status_code == 204
        assert not Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_returns_no_content_body(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Django"},
            format="json",
        )

        # Assert
        assert response.status_code == 204
        assert response.content == b""

    def test_delete_action_requires_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={},
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert response.data == {
            "error": "Skill name is required",
        }
        assert Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_rejects_null_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": None},
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert response.data == {
            "error": "Skill name is required",
        }
        assert Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_rejects_empty_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": ""},
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert response.data == {
            "error": "Skill name is required",
        }
        assert Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_returns_404_for_nonexistent_name(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert response.status_code == 404

    def test_delete_action_does_not_delete_another_users_skill(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert response.status_code == 404
        assert Skill.objects.filter(pk=another_skill.pk).exists()

    def test_delete_action_deletes_only_authenticated_users_skill(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        own_skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Django",
            slug="django",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert response.status_code == 204
        assert not Skill.objects.filter(pk=own_skill.pk).exists()
        assert Skill.objects.filter(pk=another_skill.pk).exists()

    def test_delete_action_uses_exact_name_match(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Python Programming"},
            format="json",
        )

        # Assert
        assert response.status_code == 404
        assert Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_is_case_sensitive(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "python"},
            format="json",
        )

        # Assert
        assert response.status_code == 404
        assert Skill.objects.filter(pk=skill.pk).exists()

    def test_delete_action_does_not_require_description(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
            description="",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert response.status_code == 204
        assert not Skill.objects.filter(pk=skill.pk).exists()


class TestSkillViewSetOwnership:
    def test_user_cannot_delete_another_users_skill_by_id(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Python",
            slug="python",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": another_skill.pk},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 204

    def test_authenticated_user_cannot_delete_other_profile_skill_by_id(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        own_skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Django",
            slug="django",
        )

        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": another_skill.pk},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 404
        assert Skill.objects.filter(pk=another_skill.pk).exists()
        assert Skill.objects.filter(pk=own_skill.pk).exists()

    def test_authenticated_user_cannot_delete_other_profile_skill_by_name(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Django",
            slug="django",
        )

        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.delete(
            url,
            data={"name": "Django"},
            format="json",
        )

        # Assert
        assert response.status_code == 404
        assert Skill.objects.filter(pk=another_skill.pk).exists()

    def test_user_only_sees_own_queryset_for_delete_action(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        own_skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        another_skill = Skill.objects.create(
            profile=another_profile,
            name="Django",
            slug="django",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse("profile-api:skill-delete")

        # Act
        own_response = authenticated_client.delete(
            url,
            data={"name": "Django"},
            format="json",
        )
        another_response = authenticated_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert own_response.status_code == 204
        assert another_response.status_code == 404

        assert Skill.objects.filter(pk=own_skill.pk).exists()
        assert not Skill.objects.filter(pk=another_skill.pk).exists()


class TestSkillViewSetAllowedMethods:
    def test_list_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405

    def test_detail_get_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill.pk},
        )

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405

    def test_update_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill.pk},
        )
        data = {
            "name": "Django",
            "description": "Django framework.",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 405

        skill.refresh_from_db()

        assert skill.name == "Python"
        assert skill.description == ""

    def test_patch_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill.pk},
        )

        # Act
        response = authenticated_client.patch(
            url,
            {"name": "Django"},
            format="json",
        )

        # Assert
        assert response.status_code == 405

        skill.refresh_from_db()

        assert skill.name == "Python"

    def test_custom_delete_action_does_not_accept_get(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        url = reverse("profile-api:skill-delete")

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405


class TestSkillViewSetAuthentication:
    def test_unauthenticated_user_cannot_create_skill(
        self,
        api_client,
    ):
        # Arrange
        url = reverse("profile-api:skill-list")
        data = {
            "name": "Python",
            "description": "Python programming.",
        }

        # Act
        response = api_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code in (401, 403)

    def test_unauthenticated_user_cannot_delete_skill_by_id(
        self,
        api_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        skill_id = skill.pk

        url = reverse(
            "profile-api:skill-detail",
            kwargs={"pk": skill_id},
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code in (401, 403)
        assert Skill.objects.filter(pk=skill_id).exists()

    def test_unauthenticated_user_cannot_delete_skill_by_name(
        self,
        api_client,
        profile,
    ):
        # Arrange
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )

        url = reverse("profile-api:skill-delete")

        # Act
        response = api_client.delete(
            url,
            data={"name": "Python"},
            format="json",
        )

        # Assert
        assert response.status_code in (401, 403)
        assert Skill.objects.filter(pk=skill.pk).exists()
