from django.core.files.uploadedfile import SimpleUploadedFile


def image_file(
    name: str = "image.jpg",
    content: bytes = b"file_content",
    content_type: str = "image/jpeg",
):
    return SimpleUploadedFile(
        name=name,
        content=content,
        content_type=content_type,
    )
