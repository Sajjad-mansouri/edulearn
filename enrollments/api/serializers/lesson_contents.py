from rest_framework import serializers

from curriculums.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["file", "file_size"]
