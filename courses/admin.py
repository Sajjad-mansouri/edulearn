# Register your models here.
from django.contrib import admin

from .models import Category, Course

admin.site.register(Category)
admin.site.register(Course)
