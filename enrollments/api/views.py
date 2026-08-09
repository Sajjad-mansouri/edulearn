from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response

from courses.models import Course
from enrollments.models import Enrollment


class CurrentUserEnrollmentStatus(GenericAPIView):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            is_enrolled = Enrollment.objects.filter(
                course=course, user=request.user
            ).exists()
            return Response({"is_enrolled": is_enrolled})

        return Response({"is_enrolled": False})
