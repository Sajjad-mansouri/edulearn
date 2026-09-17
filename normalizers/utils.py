"""
Utility functions shared across normalizers.

These handle the repetitive task of navigating Django's QueryDict
and extracting structured data from flat indexed keys.
"""

import logging
from collections.abc import Generator
from typing import Any

from django.core.files.uploadedfile import UploadedFile
from django.http import QueryDict

logger = logging.getLogger(__name__)


def iterate_indexed(
    query_dict: QueryDict, prefix: str, required_field: str | None = None
) -> Generator[tuple[int, str], None, None]:
    """
    Generator that yields (index, base_key) for indexed items in QueryDict.

    Handles the common pattern of finding items like:
        sections[0], sections[1], sections[2], etc.

    Args:
        query_dict: The QueryDict containing form data
        prefix: Base prefix without index (e.g., 'sections')
        required_field: If provided, only yields items where this field exists

    Yields:
        Tuple of (index, formatted_base_key)

    Example:
        >>> for i, base in iterate_indexed(query_dict, 'sections', 'id'):
        ...     section_id = query_dict.get(f"{base}.id")
    """
    i = 0
    while True:
        base_key = f"{prefix}[{i}]"

        if required_field:
            # Check if required field exists for this index
            check_key = f"{base_key}.{required_field}"
            if check_key not in query_dict:
                break
        else:
            # Check if any field exists with this prefix
            if not any(k.startswith(base_key) for k in query_dict.keys()):
                break

        yield i, base_key
        i += 1


def get_value(query_dict: QueryDict, key: str, default: Any = "") -> Any:
    """
    Get a value from QueryDict, returning default for empty/missing values.

    Unlike direct dict access, this handles:
    - Missing keys
    - Empty strings
    - The string 'null' from JavaScript frontends

    Args:
        query_dict: The QueryDict
        key: Field key to retrieve
        default: Value to return if key not found or empty

    Returns:
        The field value or default
    """
    if key not in query_dict:
        return default

    value = query_dict[key]

    # Handle empty values and JS null strings
    if not value or value == "null":
        return default
    if key == "duration":
        print("value of", key, "is", value)
    return value


def get_file(query_dict: QueryDict, key: str) -> UploadedFile | None:
    """
    Get an uploaded file from QueryDict.

    Django stores uploaded files as UploadedFile objects in QueryDict.
    This safely extracts them, handling missing files and JS null values.

    Args:
        query_dict: The QueryDict
        key: File field key

    Returns:
        UploadedFile object or None
    """
    if key not in query_dict:
        return None

    value = query_dict[key]

    if not value or value == "null":
        return None

    # Django already parsed the file upload
    if isinstance(value, UploadedFile):
        return value

    return None


def extract_array(
    query_dict: QueryDict,
    field_name: str,
    fields_map: dict = None,
    value_key: str = None,
    from_field_name: str = None,
) -> tuple[list, list]:
    """
    Extract array values from indexed QueryDict fields.

    Handles multiple formats:

    1. Simple values:
       outcomes[0] = "Learn Python"
       → [{"description": "Learn Python"}]

    2. Multiple fields per item:
       outcomes[0].description = "Learn Python"
       outcomes[0].order = 1
       → [{"description": "Learn Python", "order": "1"}]

    3. Custom field mapping:
       tags[0] = "Python"
       → [{"name": "Python"}]  (using value_key='name')

    Args:
        query_dict: The QueryDict
        field_name: Base field name (e.g., 'outcomes')
        fields_map: Dict mapping form field names to output keys
                    e.g., {'description': 'description', 'order': 'order'}
        value_key: Simple key name for single-value items (legacy)

    Returns:
        List of dictionaries
    """
    items = []
    deleted_items_ids = []

    for i, _ in iterate_indexed(query_dict, field_name):
        item = {}

        if fields_map:
            # Complex case: extract multiple fields per item
            deleted_item = query_dict.get(f"{field_name}[{i}].deleted")
            if deleted_item:
                deleted_items_ids.append(query_dict.get(f"{field_name}[{i}].id"))
                continue
            for form_field, output_key in fields_map.items():
                key = f"{field_name}[{i}].{form_field}"
                value = query_dict.get(key, "")
                if value and value != "null":
                    item[output_key] = value

            if item:  # Only add if we found some fields
                items.append(item)

        elif value_key:
            # Simple case: single value per item (legacy)
            key = f"{field_name}[{i}]"
            value = query_dict.get(key, "")
            if value and value != "null":
                items.append({value_key: value})

        else:
            # Default: use 'description' as key
            key = f"{field_name}[{i}]"
            value = query_dict.get(key, "")
            if value and value != "null":
                items.append({"description": value})

    return items, deleted_items_ids


def extract_tags(query_dict: QueryDict, field_name: str = "tags") -> tuple[list, list]:
    """
    Extract tags with 'name' key.
    Now just a convenience wrapper around extract_array.
    """
    tags, deleted_tags_ids = extract_array(
        query_dict, field_name, fields_map={"id": "id", "name": "name"}
    )
    return tags, deleted_tags_ids


def extract_attachments(
    query_dict: QueryDict, base_key: str = "attachments", fields_map: dict = None
) -> tuple[list, list]:
    """
    Extract file attachments from QueryDict.
    delete attachment that deleted flag is true else prepare to create new attachment
    Course Attachments come as indexed file fields:
        base_key = attachments
        existing course attachment:
            attachments[0].id = <UploadedFile>
            'attachments[0].deleted': ['true']
        new course attachment:
            attachments[0].file = <UploadedFile>

        attachments[1] = <UploadedFile>

    Course Attachments :
        base_key = 'sections[0].lessons[4].content.attachments
        existing course lesson attachment:

            'sections[0].lessons[4].content.attachments[1].id': ['52']
            'sections[0].lessons[4].content.attachments[0].deleted': ['true']
        new course attachment:
                    'sections[0].lessons[4].content.attachments[2].file': [<InMemoryUploadedFile: test.png (image/png)>]}>
    Args:
        query_dict: The QueryDict
        base_key: Base key for attachments

    Returns:
        List of {'file': UploadedFile} dictionaries
        list of deleted attachments ids
    """
    attachments = []
    deleted_attachments_ids = []

    for _i, attachment_base_key in iterate_indexed(query_dict, base_key):
        attachment = {}

        if get_value(query_dict, f"{attachment_base_key}.deleted"):
            deleted_attachments_ids.append(
                get_value(query_dict, f"{attachment_base_key}.id")
            )
            continue
        if get_value(query_dict, f"{attachment_base_key}.file"):
            for form_field, output_key in fields_map.items():
                key = f"{attachment_base_key}.{form_field}"
                value = query_dict.get(key, "")
                if value and value != "null":
                    attachment[output_key] = value
            if attachment:
                attachments.append(attachment)

    return attachments, deleted_attachments_ids
