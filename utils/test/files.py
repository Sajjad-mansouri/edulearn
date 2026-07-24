from django.core.files.uploadedfile import SimpleUploadedFile


def file_field(
    name: str = "file.pdf",
    content: bytes = b"test file",
    content_type: str = "application/octet-stream",
):
    return SimpleUploadedFile(
        name=name,
        content=content,
        content_type=content_type,
    )
