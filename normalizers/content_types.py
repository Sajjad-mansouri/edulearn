"""
Content type normalizers.

Each content type (video, article, quiz, etc.) has its own normalizer function.
These are registered in CONTENT_NORMALIZERS dict for easy dispatch.
"""

import logging

from django.http import QueryDict

from . import constants as C
from .utils import extract_attachments, get_file, get_value, iterate_indexed

logger = logging.getLogger(__name__)


def normalize_video_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> tuple[dict, dict]:
    """
    Normalize video lesson content from flat form data.
    'sections[0].lessons[1].content.video.video_file': [<InMemoryUploadedFile: test.mp4 (video/mp4)>]
    'sections[0].lessons[1].content.captions[0].file': [<InMemoryUploadedFile: >]
    Extracts video URL, file, captions, transcript, and text content.
    """

    base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}]"

    # Normalize video captions/subtitles
    captions = []
    captions_deleted_ids = []
    captions_base = f"{base}.{C.PREFIX_CONTENT}.{C.CAPTIONS_PREFIX}"

    for _i, cap_base in iterate_indexed(query_dict, captions_base):
        caption_id = get_value(query_dict, f"{cap_base}.id")
        deleted = get_value(query_dict, f"{cap_base}.deleted")
        file = get_file(query_dict, f"{cap_base}.{C.CAPTION_FILE}")
        if file is not None:
            caption = {
                "file": file,
                "language": get_value(query_dict, f"{cap_base}.{C.CAPTION_LANGUAGE}"),
                "label": get_value(query_dict, f"{cap_base}.{C.CAPTION_LABEL}"),
                "is_default": get_value(
                    query_dict, f"{cap_base}.{C.CAPTION_IS_DEFAULT}"
                ),
                "file_format": get_value(query_dict, f"{cap_base}.{C.CAPTION_FORMAT}"),
            }
            if caption_id:
                caption["id"] = caption_id

            captions.append(caption)
        if deleted:
            captions_deleted_ids.append(caption_id)

    video_base = f"{base}.{C.PREFIX_CONTENT}.{C.CONTENT_TYPE_VIDEO}"
    file = get_file(query_dict, f"{video_base}.{C.CONTENT_VIDEO_FILE}")

    content_id = get_value(query_dict, f"{base}.{C.PREFIX_CONTENT}.id")
    content = {
        "content_type": C.CONTENT_TYPE_VIDEO,
        "video": {
            "external_url": get_value(
                query_dict, f"{video_base}.{C.CONTENT_VIDEO_URL}"
            ),
            "text": get_value(query_dict, f"{video_base}.{C.CONTENT_TEXT_CONTENT}"),
            "transcript": get_value(query_dict, f"{video_base}.{C.CONTENT_TRANSCRIPT}"),
            "captions": captions,
        },
    }
    if content_id:
        content["id"] = content_id

    if file is not None:
        content["video"]["video_file"] = file

    return content, captions_deleted_ids


def normalize_article_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize article lesson content from flat form data.
    'sections[0].lessons[0].content.id': ['92', '92']
    'sections[0].lessons[0].content.article.id': ['129']
    'sections[0].lessons[0].content.article.body'

    Article content is simple - just a text body.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"
    article_id = get_value(query_dict, f"{content_base}.{C.CONTENT_TYPE_ARTICLE}.id")
    content = {
        "content_type": C.CONTENT_TYPE_ARTICLE,
        "article": {
            "body": get_value(
                query_dict, f"{content_base}.{C.CONTENT_TYPE_ARTICLE}.body"
            ),
        },
    }
    content_id = get_value(query_dict, f"{content_base}.id")
    if content_id:
        content["id"] = content_id
    if article_id:
        content["article"]["id"] = article_id
    return content


def normalize_file_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize file lesson content from flat form data.

    Handles both uploaded files and external file URLs.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"
    file_content_base = f"{content_base}.{C.PREFIX_CONTENT_FILE}"
    file = get_file(query_dict, f"{file_content_base}.{C.CONTENT_FILE}")

    file_content_id = get_value(query_dict, f"{file_content_base}.id")
    content_id = get_value(query_dict, f"{content_base}.id")

    content = {
        "content_type": C.CONTENT_TYPE_FILE,
        "file": {
            "file": file,
            "file_url": get_value(
                query_dict, f"{file_content_base}.{C.CONTENT_FILE_URL}"
            ),
        },
    }

    if file_content_id:
        content["file"]["id"] = file_content_id
    if content_id:
        content["id"] = content_id
    return content


def normalize_quiz_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize quiz lesson content from flat form data.

    Handles quiz settings and nested questions with type-specific options.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"
    quiz_base = f"{content_base}.{C.CONTENT_QUIZ_SETTINGS}"
    content_id = get_value(query_dict, f"{content_base}.id")
    quiz_id = get_value(query_dict, f"{quiz_base}.id")
    content = {
        "content_type": C.CONTENT_TYPE_QUIZ,
        "quiz": {
            "id": get_value(query_dict, f"{quiz_base}.id"),
            "instructions": get_value(query_dict, f"{quiz_base}.{C.QUIZ_INSTRUCTIONS}"),
            "passing_score": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_PASSING_SCORE}"
            ),
            "time_limit": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_TIME_LIMIT}", None
            ),
            "max_attempts": get_value(query_dict, f"{quiz_base}.{C.QUIZ_MAX_ATTEMPTS}"),
            "shuffle_questions": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_SHUFFLE_QUESTIONS}"
            ),
            "shuffle_choices": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_SHUFFLE_CHOICES}"
            ),
            "show_correct_answers": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_SHOW_CORRECT}"
            ),
            "questions": _normalize_quiz_questions(query_dict, content_base),
        },
    }

    if content_id:
        content["id"] = content_id
    if quiz_id:
        content["quiz"]["id"] = quiz_id
    return content


def _normalize_quiz_questions(query_dict: QueryDict, content_base: str) -> list:
    """
    Normalize quiz questions with type-specific data.
    'sections[0].lessons[0].content.questions[0].id': ['34'],

    Different question types have different structures:
    - single_choice/multiple_choice: options with correct flags
    - true_false: boolean correct answer
    - short_answer: list of accepted answers
    """
    questions = []
    questions_base = f"{content_base}.{C.QUIZ_QUESTIONS}"

    for _i, question_base in iterate_indexed(
        query_dict, questions_base, C.QUESTION_TYPE
    ):
        question_type = get_value(query_dict, f"{question_base}.{C.QUESTION_TYPE}")
        question_id = get_value(query_dict, f"{question_base}.id")
        question = {
            "text": get_value(query_dict, f"{question_base}.{C.QUESTION_TEXT}"),
            "question_type": question_type,
            "difficulty": get_value(
                query_dict, f"{question_base}.{C.QUESTION_DIFFICULTY}"
            ),
            "points": get_value(query_dict, f"{question_base}.{C.QUESTION_POINTS}"),
            "explanation": get_value(
                query_dict, f"{question_base}.{C.QUESTION_EXPLANATION}"
            ),
            "is_required": get_value(
                query_dict, f"{question_base}.{C.QUESTION_REQUIRED}"
            ),
            "estimated_time": get_value(
                query_dict, f"{question_base}.{C.QUESTION_TIME}"
            ),
            "order": get_value(query_dict, f"{question_base}.{C.QUESTION_ORDER}"),
        }
        if question_id:
            question["id"] = question_id
        # Add type-specific data
        if question_type in ("single_choice", "multiple_choice"):
            question["choices"] = _normalize_question_choices(
                query_dict,
                question_base,
                question_type,
                fields_map={"text": "text", "is_correct": "is_correct"},
            )
        elif question_type == "true_false":
            question["boolean_answer"] = {
                "answer": get_value(query_dict, f"{question_base}.{C.QUESTION_CORRECT}")
            }
        elif question_type == "short_answer":
            question["accepted_answers"] = _normalize_accepted_answers(
                query_dict, question_base, fields_map={"answer": "answer"}
            )

        questions.append(question)

    return questions


def _normalize_question_choices(
    query_dict: QueryDict, question_base: str, question_type: str, fields_map: dict
) -> list:
    """
    Normalize options for choice-based questions.

    Determines which options are correct based on question type:
    - single_choice: one correct option
    - multiple_choice: potentially multiple correct options
    """
    choices = []

    # Build options list
    choices_base = f"{question_base}.{C.QUESTION_OPTIONS}"
    for _i, option_base in iterate_indexed(query_dict, choices_base):
        choice = {}
        choice_id = query_dict.get(f"{option_base}.id", "")
        for form_field, output_key in fields_map.items():
            key = f"{option_base}.{form_field}"
            value = query_dict.get(key, "")
            if value and value != "null":
                choice[output_key] = value
        if choice_id:
            choice["id"] = choice_id
        if choice:
            choices.append(choice)
    return choices


def _normalize_accepted_answers(
    query_dict: QueryDict, question_base: str, fields_map: dict
) -> list:
    """
    Normalize accepted answers for short answer questions.

    Each accepted answer is a possible correct response.
    """
    answers = []
    answers_base = f"{question_base}.{C.QUESTION_ACCEPTED_ANSWERS}"

    for _i, answer_base in iterate_indexed(query_dict, answers_base):
        accepted = {}
        answer_id = query_dict.get(f"{answers_base}.id")
        for form_field, output_key in fields_map.items():
            key = f"{answer_base}.{form_field}"
            value = query_dict.get(key, "")
            if value and value != "null":
                accepted[output_key] = value
        if answer_id:
            accepted["id"] = answer_id
        if accepted:
            answers.append(accepted)
    return answers


def normalize_assignment_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize assignment lesson content from flat form data.

    Includes instructions, scoring, submission rules, and due dates.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"
    content_id = get_value(query_dict, f"{content_base}.id")
    assignment_id = get_value(query_dict, f"{content_base}.assignment.id")
    content = {
        "content_type": C.CONTENT_TYPE_ASSIGNMENT,
        "assignment": {
            "instructions": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_INSTRUCTIONS}"
            ),
            "max_score": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_MAX_SCORE}"
            ),
            "allow_late_submission": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_ALLOW_LATE}"
            ),
            "max_attempts": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_MAX_ATTEMPTS}"
            ),
            "accepted_file_types": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_FILE_TYPES}"
            ),
            "max_file_size_mb": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_FILE_SIZE}"
            ),
            "due_date": get_value(
                query_dict, f"{content_base}.assignment.{C.ASSIGNMENT_DUE_DATE}"
            ),
        },
    }

    if content_id:
        content["id"] = content_id
    if assignment_id:
        content["assignment"]["id"] = assignment_id

    return content


# Registry mapping content types to their normalizers
CONTENT_NORMALIZERS = {
    C.CONTENT_TYPE_VIDEO: normalize_video_content,
    C.CONTENT_TYPE_ARTICLE: normalize_article_content,
    C.CONTENT_TYPE_QUIZ: normalize_quiz_content,
    C.CONTENT_TYPE_ASSIGNMENT: normalize_assignment_content,
    C.CONTENT_TYPE_FILE: normalize_file_content,
}


def normalize_lesson_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> tuple[list, list]:
    """
    Normalize content for a single lesson based on its type.

    Dispatches to the appropriate content normalizer and adds attachments.
            'sections[0].lessons[0].content.content_type': ['article']
            'sections[0].lessons[1].content.article.body': ['article of lesson 2']
    Args:
        query_dict: The QueryDict
        section_index: Parent section index
        lesson_index: Lesson index within the section

    Returns:
        List containing the normalized content dict (wrapped in list for consistency)
    """
    base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}]"
    content_type = get_value(
        query_dict, f"{base}.{C.PREFIX_CONTENT}.{C.FIELD_LESSON_TYPE}"
    )

    if not content_type:
        logger.warning(
            f"No content type specified for section {section_index}, lesson {lesson_index}"
        )
        return [], []

    normalizer = CONTENT_NORMALIZERS.get(content_type)
    if not normalizer:
        logger.warning(
            f"Unknown content type '{content_type}' for section {section_index}, lesson {lesson_index}"
        )
        return [], []

    # Normalize the content
    deleted_attachments_ids = []
    captions_deleted_ids = []
    content = normalizer(query_dict, section_index, lesson_index)
    # Add any file attachments to the content
    # sections[0].lessons[4].content.attachments
    attachments_base = f"{base}.{C.PREFIX_CONTENT}.{C.FIELD_ATTACHMENT_FILES}"
    if content_type == C.CONTENT_TYPE_VIDEO:
        content, captions_deleted_ids = content

    content["attachments"], deleted_attachments_ids = extract_attachments(
        query_dict, attachments_base, {"file": "file"}
    )

    return content, deleted_attachments_ids, captions_deleted_ids
