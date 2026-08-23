"""
Main course normalizer - entry point for restructuring course form data.

This module orchestrates the normalization of all course components:
- Basic fields (title, description, pricing, etc.)
- File uploads (thumbnail, promo video, trailer)
- Array fields (outcomes, prerequisites, tags, etc.)
- Nested structures (sections → lessons → content)
- Attachments
"""

from django.http import QueryDict

from . import constants as C
from .constants import (
    FIELD_CATEGORY,
    FIELD_COURSE_TRAILER,
    FIELD_DESCRIPTION,
    FIELD_DURATION,
    FIELD_LANGUAGE,
    FIELD_LEVEL,
    FIELD_OUTCOMES,
    FIELD_PREREQUISITES,
    FIELD_PRICE,
    FIELD_PRICE_DISCOUNT,
    FIELD_PRICE_TYPE,
    FIELD_PROMO_VIDEO,
    FIELD_REVIEW_STATUS,
    FIELD_SEO_DESCRIPTION,
    FIELD_SEO_TITLE,
    FIELD_SHORT_DESCRIPTION,
    FIELD_STATUS,
    FIELD_SUBCATEGORY,
    FIELD_SUBTITLE,
    FIELD_TAGS,
    FIELD_TARGET_AUDIENCE,
    FIELD_THUMBNAIL,
    FIELD_TITLE,
    FIELD_VERSION,
    FIELD_VERSION_NOTE,
    FIELD_VISIBILITY,
)
from .section import normalize_sections
from .utils import extract_array, extract_attachments, extract_tags, get_file, get_value


def normalize_course_data(query_dict: QueryDict) -> tuple[dict, dict]:
    """
    Normalize flat multipart/form-data into nested course structure.

    Takes Django's QueryDict (which is already parsed from the HTTP request)
    and restructures it from flat indexed keys like:
        sections[0].title
        sections[0].lessons[1].content.videoUrl

    Into nested dicts that DRF serializers can understand:
        {
            "sections": [
                {
                    "title": "...",
                    "lessons": [
                        {
                            "content": {
                                "video_url": "..."
                            }
                        }
                    ]
                }
            ]
        }

    IMPORTANT: This function does NOT:
    - Parse types (strings stay strings, files stay as UploadedFile)
    - Validate data (no business rules applied)
    - Convert formats (durations stay as "00:12:00")

    All type conversion and validation is handled by DRF serializers.

    Args:
        query_dict: Django QueryDict from request.POST / request.FILES

    Returns:
        Fully normalized nested dict ready for serializer validation
    """
    deleted_ids_dict = {}

    # Normalize basic text fields
    course_data = _normalize_basic_fields(query_dict)

    # Normalize thumbnail uploads
    course_data.update(_normalize_file_fields(query_dict))

    # Normalize array fields (outcomes, prerequisites, etc.)
    normalized_array, deleted_ids_dict = _normalize_array_fields(
        query_dict, deleted_ids_dict
    )
    course_data.update(normalized_array)

    # Normalize SEO fields
    course_data.update(_normalize_seo_fields(query_dict))

    # Normalize nested sections (with lessons and content)
    normalized_sections, deleted_ids_dict = normalize_sections(
        query_dict, deleted_ids_dict
    )
    course_data["sections"] = normalized_sections

    # Normalize top-level attachments
    course_data["attachments"], deleted_attachments_ids = extract_attachments(
        query_dict, fields_map={"file": "file"}
    )
    deleted_ids_dict.setdefault("attachments", []).extend(deleted_attachments_ids)

    return course_data, deleted_ids_dict


def _normalize_basic_fields(query_dict: QueryDict) -> dict:
    """
    Normalize basic course-level text fields.

    Simply extracts values from QueryDict and puts them in a dict.
    Empty values become empty strings for consistency.
    """
    if get_value(query_dict, FIELD_SUBCATEGORY):
        category = get_value(query_dict, FIELD_SUBCATEGORY)
    else:
        category = get_value(query_dict, FIELD_CATEGORY)
    return {
        "title": get_value(query_dict, FIELD_TITLE),
        "subtitle": get_value(query_dict, FIELD_SUBTITLE),
        "short_description": get_value(query_dict, FIELD_SHORT_DESCRIPTION),
        "category": category,
        "subcategory": get_value(query_dict, FIELD_SUBCATEGORY),
        "level": get_value(query_dict, FIELD_LEVEL),
        "language": get_value(query_dict, FIELD_LANGUAGE),
        "duration": get_value(query_dict, FIELD_DURATION),
        "visibility": get_value(query_dict, FIELD_VISIBILITY),
        "description": get_value(query_dict, FIELD_DESCRIPTION),
        "price_type": get_value(query_dict, FIELD_PRICE_TYPE),
        "price": get_value(query_dict, FIELD_PRICE),
        "price_discount": get_value(query_dict, FIELD_PRICE_DISCOUNT, 0),
        "version": get_value(query_dict, FIELD_VERSION),
        "version_note": get_value(query_dict, FIELD_VERSION_NOTE),
        "status": get_value(query_dict, FIELD_STATUS),
        "review_status": get_value(query_dict, FIELD_REVIEW_STATUS),
        "promotional_video": get_value(query_dict, FIELD_PROMO_VIDEO),
        "course_trailer": get_value(query_dict, FIELD_COURSE_TRAILER),
    }


def _normalize_file_fields(query_dict: QueryDict) -> dict:
    """
    Normalize uploaded file fields.

    Returns UploadedFile objects as-is (serializer will handle them).
    """
    file = get_file(query_dict, FIELD_THUMBNAIL)
    if file:
        return {
            "thumbnail": file,
        }
    return {}


def _normalize_array_fields(
    query_dict: QueryDict, deleted_ids_dict: dict
) -> tuple[dict, dict]:
    """
    Normalize array-type fields from indexed flat structure.

    Converts:
        outcomes[0]="Learn X", outcomes[1]="Build Y"
    Into:
        [{"description": "Learn X"}, {"description": "Build Y"}]
    """
    outcomes, deleted_outcomes_ids = extract_array(
        query_dict,
        FIELD_OUTCOMES,
        fields_map={"description": "description", "id": "id"},
    )
    prerequisites, deleted_prerequisites_ids = extract_array(
        query_dict,
        FIELD_PREREQUISITES,
        fields_map={"description": "description", "id": "id"},
    )
    target_audiences, deleted_target_audiences_ids = extract_array(
        query_dict,
        FIELD_TARGET_AUDIENCE,
        fields_map={"description": "description", "id": "id"},
    )
    features, deleted_features_ids = extract_array(
        query_dict, C.FIELD_FEATURES, fields_map={"text": "text", "icon": "icon"}
    )

    tags, deleted_tags_ids = extract_tags(query_dict, FIELD_TAGS)
    deleted_ids_dict = {
        "outcomes": deleted_outcomes_ids,
        "prerequisites": deleted_prerequisites_ids,
        "target_audiences": deleted_target_audiences_ids,
        "tags": deleted_tags_ids,
        "features": features,
    }

    return (
        {
            C.MODEL_FIELD_OUTCOMES: outcomes,
            FIELD_PREREQUISITES: prerequisites,
            C.MODEL_FIELD_TARGET_AUDIENCE: target_audiences,
            FIELD_TAGS: tags,
            C.FIELD_FEATURES: features,
        },
        deleted_ids_dict,
    )


def _normalize_seo_fields(query_dict: QueryDict) -> dict:
    """
    Normalize SEO metadata fields.

    These are separate from basic fields for clarity and potential reuse.
    """
    return {
        "seo_title": get_value(query_dict, FIELD_SEO_TITLE),
        "seo_description": get_value(query_dict, FIELD_SEO_DESCRIPTION),
    }
