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


def normalize_sections(query_dict: QueryDict) -> list:
    """
    Normalize all sections from the QueryDict.

    Each section contains its metadata and nested lessons.

    Args:
        query_dict: The QueryDict containing form data

    Returns:
        List of normalized section dictionaries
    """
    sections = []

    for i, section_base in iterate_indexed(
        query_dict, PREFIX_SECTIONS, FIELD_SECTION_ID
    ):
        section = {
            "id": get_value(query_dict, f"{section_base}.{FIELD_SECTION_ID}"),
            "title": get_value(query_dict, f"{section_base}.{FIELD_SECTION_TITLE}"),
            "description": get_value(
                query_dict, f"{section_base}.{FIELD_SECTION_DESCRIPTION}"
            ),
            "duration": get_value(
                query_dict, f"{section_base}.{FIELD_SECTION_DURATION}"
            ),
            "lessons": normalize_lessons(query_dict, i),
        }
        sections.append(section)

    return sections
