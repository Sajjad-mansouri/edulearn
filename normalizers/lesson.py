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


def normalize_lessons(
    query_dict: QueryDict, section_index: int
) -> tuple[list, list, list]:
    """
    Normalize all lessons for a given section.

    Each lesson becomes a dict with its metadata and nested content.
            'sections[0].lessons[1].title': ['article new']
            'sections[0].lessons[1].description': ['new description']
            'sections[0].lessons[1].duration': ['10']
            'sections[0].lessons[1].preview': ['true']
            'sections[0].lessons[1].published': ['true']

    Args:
        query_dict: The QueryDict containing form data
        section_index: Index of the parent section

    Returns:
        List of normalized lesson dictionaries
    """
    lessons = []
    deleted_lessons_ids = []
    prefix = f"{PREFIX_SECTIONS}[{section_index}].{PREFIX_LESSONS}"
    lessons_deleted_attachments_ids = []
    lessons_deleted_captions_ids = []
    for i, lesson_base in iterate_indexed(query_dict, prefix, FIELD_LESSON_TITLE):
        content, deleted_attachments_ids, captions_deleted_ids = (
            normalize_lesson_content(query_dict, section_index, i)
        )
        lessons_deleted_attachments_ids.extend(deleted_attachments_ids)
        lessons_deleted_captions_ids.extend(captions_deleted_ids)

        lesson_id = get_value(query_dict, f"{lesson_base}.{FIELD_LESSON_ID}")
        lesson = {
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
            "content": content,
        }
        if lesson_id:
            lesson["id"] = lesson_id

        lessons.append(lesson)

    for _i, lesson_base in iterate_indexed(query_dict, prefix, FIELD_LESSON_ID):
        if get_value(query_dict, f"{lesson_base}.deleted"):
            deleted_lessons_ids.append(
                get_value(query_dict, f"{lesson_base}.{FIELD_LESSON_ID}")
            )

    return (
        lessons,
        deleted_lessons_ids,
        lessons_deleted_attachments_ids,
        lessons_deleted_captions_ids,
    )


def normalize_completion_criteria(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    'sections[0].lessons[1].completion_criteria.criteria_type': ['read_article']
    'sections[0].lessons[1].completion_criteria.deleted': ['false']
    """
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
