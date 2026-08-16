from rest_framework import serializers

from assessments.models import (
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionFile,
)


class AssignmentSerializer(serializers.ModelSerializer):
    maxScore = serializers.IntegerField(source="max_score")
    dueDate = serializers.DateTimeField(source="due_date")
    allowLateSubmission = serializers.BooleanField(source="allow_late_submission")
    maxAttempts = serializers.IntegerField(source="max_attempts")
    acceptedFileTypes = serializers.CharField(source="accepted_file_types")
    maxFileSizeMB = serializers.IntegerField(source="max_file_size_mb")

    class Meta:
        model = Assignment
        fields = [
            "id",
            "instructions",
            "maxScore",
            "dueDate",
            "allowLateSubmission",
            "maxAttempts",
            "acceptedFileTypes",
            "maxFileSizeMB",
        ]


class AssignmentSubmissionFileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmissionFile
        fields = ["file", "name", "size"]
        read_only_fields = ["size"]

    def get_name(self, obj):
        return obj.file_name


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    attemptNumber = serializers.IntegerField(source="attempt_number")
    submissionText = serializers.CharField(source="submission_text")
    submittedAt = serializers.DateTimeField(source="submitted_at")
    gradedAt = serializers.DateTimeField(source="graded_at")
    files = AssignmentSubmissionFileSerializer(many=True)

    class Meta:
        model = AssignmentSubmission
        fields = [
            "attemptNumber",
            "status",
            "submissionText",
            "files",
            "score",
            "feedback",
            "submittedAt",
            "gradedAt",
        ]
