"""
Section normalizer - restructures flat section data into nested dicts.
"""

import logging

from django.http import QueryDict

from .constants import (
    FIELD_SECTION_DESCRIPTION,
    FIELD_SECTION_DURATION,
    FIELD_SECTION_ID,
    FIELD_SECTION_TITLE,
    PREFIX_SECTIONS,
)
from .lesson import normalize_lessons
from .utils import get_value, iterate_indexed

logger = logging.getLogger(__name__)


def normalize_sections(
    query_dict: QueryDict, deleted_ids_dict: dict
) -> tuple[list, list]:
    """
    Normalize all sections from the QueryDict.

    Each section contains its metadata and nested lessons.

    Args:
        query_dict: The QueryDict containing form data

    Returns:
        List of normalized section dictionaries
    """
    sections = []
    deleted_sections_ids = []
    sections_deleted_lessons_ids = []
    sections_deleted_attachments_ids = []
    sections_deleted_captions_ids = []

    for i, section_base in iterate_indexed(
        query_dict, PREFIX_SECTIONS, FIELD_SECTION_TITLE
    ):
        (
            lessons,
            deleted_lessons_ids,
            deleted_attachments_ids,
            lessons_deleted_captions_ids,
        ) = normalize_lessons(query_dict, i)

        sections_deleted_lessons_ids += deleted_lessons_ids
        sections_deleted_attachments_ids += deleted_attachments_ids
        sections_deleted_captions_ids += lessons_deleted_captions_ids

        section = {
            "title": get_value(query_dict, f"{section_base}.{FIELD_SECTION_TITLE}"),
            "description": get_value(
                query_dict, f"{section_base}.{FIELD_SECTION_DESCRIPTION}"
            ),
            "duration": get_value(
                query_dict, f"{section_base}.{FIELD_SECTION_DURATION}"
            ),
            "lessons": lessons,
        }
        section_id = get_value(query_dict, f"{section_base}.{FIELD_SECTION_ID}")
        if section_id:
            section["id"] = section_id
        sections.append(section)
    for _i, section_base in iterate_indexed(
        query_dict, PREFIX_SECTIONS, FIELD_SECTION_ID
    ):
        if get_value(
            query_dict,
            f"{section_base}.deleted",
            get_value(query_dict, f"{section_base}.deleted"),
        ):
            deleted_sections_ids.append(
                get_value(query_dict, f"{section_base}.{FIELD_SECTION_ID}")
            )
    deleted_ids_dict["sections"] = deleted_sections_ids
    deleted_ids_dict["lessons"] = sections_deleted_lessons_ids
    deleted_ids_dict["attachments"] = sections_deleted_attachments_ids
    deleted_ids_dict["captions"] = sections_deleted_captions_ids

    return sections, deleted_ids_dict
