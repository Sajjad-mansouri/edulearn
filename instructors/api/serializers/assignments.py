from rest_framework import serializers

from assessments.models import Assignment, AssignmentSubmission


class InstructorAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()
    student_avatar = serializers.SerializerMethodField()
    assignment_name = serializers.SerializerMethodField()
    assignment_desc = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    course_slug = serializers.SerializerMethodField()
    letter_grade = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "student_name",
            "student_email",
            "student_avatar",
            "assignment_name",
            "assignment_desc",
            "course_name",
            "course_slug",
            "status",
            "submitted_at",
            "graded_at",
            "score",
            "letter_grade",
            "attempt_number",
            "feedback",
            "submission_text",
            "files",
        ]

    def get_student_name(self, obj):
        return obj.enrollment.user.get_full_name()

    def get_student_email(self, obj):
        return obj.enrollment.user.email

    def get_student_avatar(self, obj):
        request = self.context["request"]
        avatar = obj.enrollment.user.profile.get_avatar()
        return request.build_absolute_uri(avatar)

    def get_assignment_name(self, obj):
        return obj.assignment.content.lesson.title

    def get_assignment_desc(self, obj):
        return obj.assignment.instructions

    def get_course_name(self, obj):
        return obj.enrollment.course.title

    def get_course_slug(self, obj):
        return obj.enrollment.course.slug

    def get_letter_grade(self, obj):
        return obj.get_letter_grade()

    def get_files(self, obj):
        request = self.context["request"]
        return [
            {
                "id": submission_file.id,
                "name": submission_file.file.name.split("/")[-1],
                "path": request.build_absolute_uri(submission_file.file.url),
                "size": submission_file.file.size,
                "uploaded_at": submission_file.uploaded_at,
            }
            for submission_file in obj.files.all()
        ]
