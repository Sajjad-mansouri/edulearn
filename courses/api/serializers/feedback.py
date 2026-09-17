from rest_framework import serializers

from courses.models import CourseFeedback, CourseFeedbackInteraction


class CourseFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    helpful_count = serializers.IntegerField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = CourseFeedback
        fields = [
            "id",
            "user_name",
            "user_avatar",
            "rating",
            "comment",
            "created_at",
            "helpful_count",
            "user_has_liked",
            "is_owner",
        ]

    def get_user_name(self, obj):
        return obj.enrollment.user.username

    def get_user_avatar(self, obj):
        return obj.enrollment.user.avatar

    def get_user_has_liked(self, obj):
        request = self.context["request"]
        if request.user.is_anonymous:
            return False

        return CourseFeedbackInteraction.objects.filter(
            feedback=obj, enrollment__user=request.user
        ).exists()

    def get_is_owner(self, obj):
        request = self.context["request"]
        return obj.enrollment.user == request.user


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFeedback
        fields = [
            "enrollment",
            "rating",
            "comment",
        ]
