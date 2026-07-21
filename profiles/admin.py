# Register your models here.
from django.contrib import admin

from .models import (
    Education,
    Experience,
    InstructorProfile,
    Language,
    Profile,
    Skill,
    SocialLink,
    StudentProfile,
)

admin.site.register(Profile)
admin.site.register(InstructorProfile)
admin.site.register(StudentProfile)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(SocialLink)
admin.site.register(Language)
