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
) -> dict:
    """
    Normalize video lesson content from flat form data.

    Extracts video URL, file, captions, transcript, and text content.
    """
    print("query_dict\n\n", query_dict, "\n\n")
    base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}]"
    content_base = f"{base}.{C.PREFIX_CONTENT}"

    # Normalize video captions/subtitles
    captions = []
    captions_base = f"{content_base}.{C.CAPTIONS_PREFIX}"

    for _i, cap_base in iterate_indexed(query_dict, captions_base, C.CAPTION_FILE):
        captions.append(
            {
                "language": get_value(query_dict, f"{cap_base}.{C.CAPTION_LANGUAGE}"),
                "label": get_value(query_dict, f"{cap_base}.{C.CAPTION_LABEL}"),
                "file_name": get_value(query_dict, f"{cap_base}.{C.CAPTION_FILE_NAME}"),
                "file_size": get_value(query_dict, f"{cap_base}.{C.CAPTION_FILE_SIZE}"),
                "is_default": get_value(
                    query_dict, f"{cap_base}.{C.CAPTION_IS_DEFAULT}"
                ),
                "file": get_file(query_dict, f"{cap_base}.{C.CAPTION_FILE}"),
                "file_format": get_value(query_dict, f"{cap_base}.{C.CAPTION_FORMAT}"),
            }
        )

    return {
        "content_type": C.CONTENT_TYPE_VIDEO,
        "video_content": {
            "external_url": get_value(
                query_dict, f"{content_base}.{C.CONTENT_VIDEO_URL}"
            ),
            "duration": get_value(query_dict, f"{base}.{C.FIELD_LESSON_DURATION}"),
            "text": get_value(query_dict, f"{content_base}.{C.CONTENT_TEXT_CONTENT}"),
            "transcript": get_value(
                query_dict, f"{content_base}.{C.CONTENT_TRANSCRIPT}"
            ),
            "captions": captions,
            "video_file": get_file(
                query_dict, f"{content_base}.{C.CONTENT_VIDEO_FILE}"
            ),
        },
    }


def normalize_article_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize article lesson content from flat form data.

    Article content is simple - just a text body.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"

    return {
        "content_type": C.CONTENT_TYPE_ARTICLE,
        "article_content": {
            "body": get_value(query_dict, f"{content_base}.{C.CONTENT_TEXT}"),
        },
    }


def normalize_file_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize file lesson content from flat form data.

    Handles both uploaded files and external file URLs.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"

    return {
        "content_type": C.CONTENT_TYPE_FILE,
        "file_content": {
            "file_url": get_value(query_dict, f"{content_base}.{C.CONTENT_FILE_URL}"),
            "file": get_file(query_dict, f"{content_base}.{C.CONTENT_FILE}"),
        },
    }


def normalize_quiz_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize quiz lesson content from flat form data.

    Handles quiz settings and nested questions with type-specific options.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"
    quiz_base = f"{content_base}.{C.CONTENT_QUIZ_SETTINGS}"

    return {
        "content_type": C.CONTENT_TYPE_QUIZ,
        "quiz_content": {
            "instructions": get_value(query_dict, f"{quiz_base}.{C.QUIZ_INSTRUCTIONS}"),
            "passing_score": get_value(
                query_dict, f"{quiz_base}.{C.QUIZ_PASSING_SCORE}"
            ),
            "time_limit": get_value(query_dict, f"{quiz_base}.{C.QUIZ_TIME_LIMIT}"),
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


def _normalize_quiz_questions(query_dict: QueryDict, content_base: str) -> list:
    """
    Normalize quiz questions with type-specific data.

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

        # Add type-specific data
        if question_type in ("single_choice", "multiple_choice"):
            question["options"] = _normalize_question_options(
                query_dict, question_base, question_type
            )
        elif question_type == "true_false":
            question["boolean_answer"] = {
                "answer": get_value(query_dict, f"{question_base}.{C.QUESTION_CORRECT}")
            }
        elif question_type == "short_answer":
            question["accepted_answers"] = _normalize_accepted_answers(
                query_dict, question_base
            )

        questions.append(question)

    return questions


def _normalize_question_options(
    query_dict: QueryDict, question_base: str, question_type: str
) -> list:
    """
    Normalize options for choice-based questions.

    Determines which options are correct based on question type:
    - single_choice: one correct option
    - multiple_choice: potentially multiple correct options
    """
    options = []

    # Collect correct answer indices
    correct_indexes = set()
    if question_type == "multiple_choice":
        # Multiple correct answers possible
        for i, _ in iterate_indexed(
            query_dict, f"{question_base}.{C.QUESTION_CORRECT}"
        ):
            correct_value = get_value(
                query_dict, f"{question_base}.{C.QUESTION_CORRECT}[{i}]"
            )
            if correct_value:
                correct_indexes.add(correct_value)
    elif question_type == "single_choice":
        # Single correct answer
        correct_value = get_value(query_dict, f"{question_base}.{C.QUESTION_CORRECT}")
        if correct_value:
            correct_indexes.add(correct_value)

    # Build options list
    for i, option_base in iterate_indexed(
        query_dict, f"{question_base}.{C.QUESTION_OPTIONS}"
    ):
        option_text = get_value(query_dict, option_base)
        is_correct = str(i) in correct_indexes

        options.append({"text": option_text, "is_correct": is_correct})

    return options


def _normalize_accepted_answers(query_dict: QueryDict, question_base: str) -> list:
    """
    Normalize accepted answers for short answer questions.

    Each accepted answer is a possible correct response.
    """
    answers = []
    answers_base = f"{question_base}.{C.QUESTION_ACCEPTED_ANSWERS}"

    for _i, answer_base in iterate_indexed(query_dict, answers_base):
        answer_text = get_value(query_dict, answer_base)
        if answer_text:
            answers.append({"answer": answer_text})

    return answers


def normalize_assignment_content(
    query_dict: QueryDict, section_index: int, lesson_index: int
) -> dict:
    """
    Normalize assignment lesson content from flat form data.

    Includes instructions, scoring, submission rules, and due dates.
    """
    content_base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}].{C.PREFIX_CONTENT}"

    return {
        "content_type": C.CONTENT_TYPE_ASSIGNMENT,
        "assignment_content": {
            "instructions": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_INSTRUCTIONS}"
            ),
            "max_score": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_MAX_SCORE}"
            ),
            "allow_late_submission": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_ALLOW_LATE}"
            ),
            "max_attempts": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_MAX_ATTEMPTS}"
            ),
            "accepted_file_types": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_FILE_TYPES}"
            ),
            "max_file_size_mb": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_FILE_SIZE}"
            ),
            "due_date": get_value(
                query_dict, f"{content_base}.{C.ASSIGNMENT_DUE_DATE}"
            ),
        },
    }


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
) -> list:
    """
    Normalize content for a single lesson based on its type.

    Dispatches to the appropriate content normalizer and adds attachments.

    Args:
        query_dict: The QueryDict
        section_index: Parent section index
        lesson_index: Lesson index within the section

    Returns:
        List containing the normalized content dict (wrapped in list for consistency)
    """
    base = f"{C.PREFIX_SECTIONS}[{section_index}].{C.PREFIX_LESSONS}[{lesson_index}]"
    content_type = get_value(query_dict, f"{base}.{C.FIELD_LESSON_TYPE}")

    if not content_type:
        logger.warning(
            f"No content type specified for section {section_index}, lesson {lesson_index}"
        )
        return []

    normalizer = CONTENT_NORMALIZERS.get(content_type)
    if not normalizer:
        logger.warning(
            f"Unknown content type '{content_type}' for section {section_index}, lesson {lesson_index}"
        )
        return []

    # Normalize the content
    content = normalizer(query_dict, section_index, lesson_index)

    # Add any file attachments to the content
    attachments_base = f"{base}.{C.PREFIX_CONTENT}.{C.FIELD_ATTACHMENT_FILES}"
    content["attachments"] = extract_attachments(query_dict, attachments_base)

    return [content]
