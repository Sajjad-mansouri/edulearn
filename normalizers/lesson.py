"""
Lesson normalizer - restructures flat lesson data into nested dicts.
"""

import logging

from django.http import QueryDict

from . import constants as C
from .constants import (
    FIELD_LESSON_DESCRIPTION,
    FIELD_LESSON_DURATION,
    FIELD_LESSON_ID,
    FIELD_LESSON_PREVIEW,
    FIELD_LESSON_PUBLISHED,
    FIELD_LESSON_TITLE,
    PREFIX_LESSONS,
    PREFIX_SECTIONS,
)
from .content_types import normalize_lesson_content
from .utils import get_value, iterate_indexed

logger = logging.getLogger(__name__)


def normalize_lessons(query_dict: QueryDict, section_index: int) -> list:
    """
    Normalize all lessons for a given section.

    Each lesson becomes a dict with its metadata and nested content.

    Args:
        query_dict: The QueryDict containing form data
        section_index: Index of the parent section

    Returns:
        List of normalized lesson dictionaries
    """
    lessons = []
    prefix = f"{PREFIX_SECTIONS}[{section_index}].{PREFIX_LESSONS}"

    for i, lesson_base in iterate_indexed(query_dict, prefix, FIELD_LESSON_ID):
        lesson = {
            "id": get_value(query_dict, f"{lesson_base}.{FIELD_LESSON_ID}"),
            "title": get_value(query_dict, f"{lesson_base}.{FIELD_LESSON_TITLE}"),
            "description": get_value(
                query_dict, f"{lesson_base}.{FIELD_LESSON_DESCRIPTION}"
            ),
            "duration": get_value(query_dict, f"{lesson_base}.{FIELD_LESSON_DURATION}"),
            "is_published": get_value(
                query_dict, f"{lesson_base}.{FIELD_LESSON_PUBLISHED}"
            ),
            "is_preview": get_value(
                query_dict, f"{lesson_base}.{FIELD_LESSON_PREVIEW}"
            ),
            "completion_criteria": normalize_completion_criteria(
                query_dict, section_index, i
            ),
            "contents": normalize_lesson_content(query_dict, section_index, i),
        }
        lessons.append(lesson)

    return lessons


def normalize_completion_criteria(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}]"
    completion_criteria_base = f"{base}.{C.PREFIX_COMPLETION_CRITERIA}"
    criteria_type = get_value(
        query_dict, f"{completion_criteria_base}.{C.COMPLETION_CRITERIA_TYPE}"
    )
    quiz_passing_score = get_value(
        query_dict,
        f"{completion_criteria_base}.{C.COMPLETION_QUIZ_PASSING_SCORE}",
        None,
    )
    video_watch_percentage = get_value(
        query_dict,
        f"{completion_criteria_base}.{C.COMPLETION_VIDEO_WATCH_PERCENTAGE}",
        None,
    )
    return {
        "criteria_type": criteria_type,
        "quiz_passing_score": quiz_passing_score,
        "video_watch_percentage": video_watch_percentage,
    }
