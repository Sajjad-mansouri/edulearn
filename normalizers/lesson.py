"""
Lesson normalizer - restructures flat lesson data into nested dicts.
"""

import logging

from django.http import QueryDict

from .constants import (
    FIELD_LESSON_COMPLETION_RULE,
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
            "completion_criteria": get_value(
                query_dict, f"{lesson_base}.{FIELD_LESSON_COMPLETION_RULE}"
            ),
            "contents": normalize_lesson_content(query_dict, section_index, i),
        }
        lessons.append(lesson)

    return lessons
