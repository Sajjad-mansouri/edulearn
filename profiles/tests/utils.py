import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def image_file(
    name: str = "image.jpg",
    content_type: str = "image/jpeg",
):
    file = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(file, format="JPEG")
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type=content_type)
