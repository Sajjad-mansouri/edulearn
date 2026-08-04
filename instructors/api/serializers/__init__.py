from .assignments import AssignmentSubmissionSerializer
from .course import (
    CourseSerializer,
    InstructorCourseSerializer,
    InstructorFilterCoursesSerializer,
)
from .student import InstructorDashboardSerializer

__all__ = [
    "CourseSerializer",
    "InstructorCourseSerializer",
    "InstructorDashboardSerializer",
    "AssignmentSubmissionSerializer",
    "InstructorFilterCoursesSerializer",
]
