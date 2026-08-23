def normalize_course_data(query_dict):
    """
    Parse the flat QueryDict back into nested course structure
    """
    data = {}

    # Handle simple fields
    simple_fields = [
        "title",
        "subtitle",
        "short_description",
        "category",
        "subcategory",
        "level",
        "language",
        "duration",
        "visibility",
        "description",
        "price_type",
        "price",
        "price_discount",
        "seoTitle",
        "seoDescription",
        "version",
        "version_note",
        "status",
        "reviewStatus",
    ]

    for field in simple_fields:
        if field in query_dict:
            value = query_dict[field]
            # Handle empty strings
            data[field] = value if value else ""
            if field == "price_discount" and query_dict[field] == "":
                data[field] = 0
            if field == "duration":
                data[field] = f"00:{data[field]}:00"

    # Handle arrays with index notation (outcomes, prerequisites, targetAudience, tags)
    array_fields = ["outcomes", "prerequisites", "targetAudience", "tags"]
    for field in array_fields:
        data[field] = extract_array_from_querydict(query_dict, field)

    # Handle sections
    data["sections"] = extract_sections(query_dict)

    # Handle files (thumbnail, promoVideo, courseTrailer)
    if "thumbnail" in query_dict and query_dict["thumbnail"]:
        data["thumbnail"] = query_dict["thumbnail"]
    else:
        data["thumbnail"] = None

    if "promo_video" in query_dict and query_dict["promo_video"]:
        data["promotional_video"] = query_dict["promo_video"]
    else:
        data["promotional_video"] = ""

    if "course_trailer" in query_dict and query_dict["course_trailer"]:
        data["course_trailer"] = query_dict["course_trailer"]
    else:
        data["course_trailer"] = ""
    if "seoTitle" in query_dict and query_dict["seoTitle"]:
        data["seo_title"] = query_dict["seoTitle"]
    else:
        data["seo_title"] = ""

    if "seoDescription" in query_dict and query_dict["seoDescription"]:
        data["seo_description"] = query_dict["seoDescription"]
    else:
        data["seo_description"] = ""

    # Handle attachments (if any)
    data["attachments"] = extract_attachments(query_dict)

    return data


def extract_array_from_querydict(query_dict, field_name):
    """Extract array values like outcomes[0], outcomes[1], etc."""
    items = []
    i = 0
    while True:
        key = f"{field_name}[{i}]"
        if key in query_dict:
            value = query_dict[key]
            if value:  # Only add non-empty values
                if field_name == "tags":
                    items.append({"name": value})

                else:
                    items.append({"description": value})
            i += 1
        else:
            break
    return items


def extract_sections(query_dict):
    """Extract sections and their nested lessons"""
    sections = []
    section_index = 0

    while True:
        # Check if section exists
        section_id_key = f"sections[{section_index}].id"
        if section_id_key not in query_dict:
            break
        duration_min = query_dict.get(f"sections[{section_index}].duration")
        if not duration_min:
            duration_min = "00"
        section = {
            "id": int(query_dict[section_id_key][0]),
            "title": query_dict.get(f"sections[{section_index}].title", ""),
            "description": query_dict.get(f"sections[{section_index}].description", ""),
            "duration": f"00:{duration_min}:00",
            "lessons": extract_lessons(query_dict, section_index),
        }
        sections.append(section)
        section_index += 1

    return sections


def extract_lessons(query_dict, section_index):
    """Extract lessons for a specific section"""
    lessons = []
    lesson_index = 0

    while True:
        # Check if lesson exists
        lesson_id_key = f"sections[{section_index}].lessons[{lesson_index}].id"
        if lesson_id_key not in query_dict:
            break
        duration_min = query_dict.get(
            f"sections[{section_index}].lessons[{lesson_index}].duration"
        )
        if not duration_min:
            duration_min = "00"
        lesson = {
            "id": int(query_dict[lesson_id_key][0]),
            "title": query_dict.get(
                f"sections[{section_index}].lessons[{lesson_index}].title", ""
            ),
            "description": query_dict.get(
                f"sections[{section_index}].lessons[{lesson_index}].description", ""
            ),
            "is_published": query_dict.get(
                f"sections[{section_index}].lessons[{lesson_index}].published", "false"
            ).lower()
            == "true",
            "duration": f"00:{duration_min}:00",
            "is_preview": query_dict.get(
                f"sections[{section_index}].lessons[{lesson_index}].preview", "false"
            ).lower()
            == "true",
            "completion_criteria": query_dict.get(
                f"sections[{section_index}].lessons[{lesson_index}].completionRule", ""
            ),
            "contents": extract_lesson_content(query_dict, section_index, lesson_index),
        }
        lessons.append(lesson)
        lesson_index += 1

    return lessons


def extract_lesson_content(query_dict, section_index, lesson_index):
    """Extract content for a specific lesson"""
    contents = []
    content = {}
    type = query_dict.get(f"sections[{section_index}].lessons[{lesson_index}].type", "")

    content["content_type"] = type
    if type == "video":
        content["video_content"] = extract_video_content(
            query_dict, section_index, lesson_index
        )
    elif type == "file":
        content["file_content"] = extract_file_content(
            query_dict, section_index, lesson_index
        )
    elif type == "article":
        content["article_content"] = extract_article_content(
            query_dict, section_index, lesson_index
        )
    elif type == "quiz":
        content["quiz_content"] = extract_quiz_content(
            query_dict, section_index, lesson_index
        )
    elif type == "assignment":
        content["assignment_content"] = extract_assignment_content(
            query_dict, section_index, lesson_index
        )

    # Handle content attachments
    content["attachments"] = extract_attachments(
        query_dict,
        f"sections[{section_index}].lessons[{lesson_index}].content.attachment_files",
    )
    contents.append(content)
    return contents


def extract_video_captions(query_dict, section_index, lesson_index):
    captions = []
    caption_index = 0
    while True:
        # Check if lesson exists
        base_name = f"sections[{section_index}].lessons[{lesson_index}].content.captions[{caption_index}]"
        caption_file_key = f"{base_name}.file"

        if caption_file_key not in query_dict:
            break
        caption = {
            "language": query_dict.get(f"{base_name}.language", ""),
            "label": query_dict.get(f"{base_name}.label", ""),
            "file_name": query_dict.get(f"{base_name}.fileName", ""),
            "file_size": query_dict.get(f"{base_name}.fileSize", ""),
            "is_default": query_dict.get(f"{base_name}.is_default", ""),
            "file": query_dict.get(f"{base_name}.file", ""),
            "file_format": query_dict.get(f"{base_name}.file_format", ""),
        }
        captions.append(caption)
        caption_index += 1
    return captions


def extract_video_content(query_dict, section_index, lesson_index):
    duration_min = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].duration"
    )
    if not duration_min:
        duration_min = "00"
    video_content = {}

    field = "videoUrl"
    external_url = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].content.{field}", ""
    )
    video_content["external_url"] = external_url
    video_content["duration"] = f"00:{duration_min}:00"

    video_content["text"] = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].content.textContent", ""
    )
    video_content["transcript"] = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].content.transcript", ""
    )
    video_content["captions"] = extract_video_captions(
        query_dict, section_index, lesson_index
    )
    # Handle videoFile (it might be a file or 'null' string)
    video_file_key = (
        f"sections[{section_index}].lessons[{lesson_index}].content.videoFile"
    )

    if video_file_key in query_dict:
        value = query_dict[video_file_key]
        if value and value != "null":
            video_content["video_file"] = value
        else:
            video_content["video_file"] = None
    return video_content


def extract_file_content(query_dict, section_index, lesson_index):
    file_url = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].content.fileUrl", ""
    )
    file_content = {}
    file_content["file_url"] = file_url

    # Handle videoFile (it might be a file or 'null' string)
    file_key = f"sections[{section_index}].lessons[{lesson_index}].content.file"
    if file_key in query_dict:
        value = query_dict[file_key]
        if value and value != "null":
            file_content["file"] = value

        else:
            file_content["file"] = None
    return file_content


def extract_article_content(query_dict, section_index, lesson_index):
    text = query_dict.get(
        f"sections[{section_index}].lessons[{lesson_index}].content.text", ""
    )

    article_content = {"body": text}
    return article_content


def extract_attachments(query_dict, base_key="attachment_files"):
    """Extract attachments from query dict"""
    attachments = []
    i = 0

    while True:
        key = f"{base_key}[{i}]"
        if key in query_dict:
            value = query_dict[key]
            # If it's a file object, keep it; if string, parse JSON
            if value and value != "null":
                attachments.append({"file": value})
            i += 1
        else:
            break

    return attachments


def extract_quiz_content(query_dict, section_index, lesson_index):
    base_name = (
        f"sections[{section_index}].lessons[{lesson_index}].content.quizSettings"
    )
    quiz = {
        "instructions": query_dict.get(f"{base_name}.instructions"),
        "passing_score": query_dict.get(f"{base_name}.passingScore"),
        "time_limit": query_dict.get(f"{base_name}.timeLimit"),
        "max_attempts": query_dict.get(f"{base_name}.maxAttempts"),
        "shuffle_questions": query_dict.get(f"{base_name}.shuffleQuestions"),
        "shuffle_choices": query_dict.get(f"{base_name}.shuffleChoices"),
        "show_correct_answers": query_dict.get(f"{base_name}.showCorrectAnswers"),
        "questions": extract_questions(query_dict, section_index, lesson_index),
    }

    return quiz


def extract_questions(query_dict, section_index, lesson_index):
    # sections[0].lessons[0].content.questions[0].question_type
    questions = []
    base_name = f"sections[{section_index}].lessons[{lesson_index}].content.questions"
    question_index = 0
    while True:
        # Check if lesson exists
        question_key = f"{base_name}[{question_index}].question_type"

        if question_key not in query_dict:
            break

        question_type = query_dict.get(
            f"{base_name}[{question_index}].question_type", ""
        )
        estimated_time_str = query_dict.get(
            f"{base_name}[{question_index}].estimated_time", ""
        )
        if estimated_time_str != "null":
            estimated_time = f"00:{estimated_time_str}:00"
        else:
            estimated_time = "00"
        question = {
            "text": query_dict.get(f"{base_name}[{question_index}].text", ""),
            "question_type": question_type,
            "difficulty": query_dict.get(
                f"{base_name}[{question_index}].difficulty", ""
            ),
            "points": query_dict.get(f"{base_name}[{question_index}].points", ""),
            "explanation": query_dict.get(
                f"{base_name}[{question_index}].explanation", ""
            ),
            "is_required": query_dict.get(
                f"{base_name}[{question_index}].is_required", ""
            ),
            "estimated_time": estimated_time,
            "order": query_dict.get(f"{base_name}[{question_index}].order", ""),
        }
        if question_type in ["single_choice", "multiple_choice"]:
            question["options"] = extract_question_options(
                question_type, query_dict, base_key=f"{base_name}[{question_index}]"
            )
        if question_type == "true_false":
            answer = query_dict.get(f"{base_name}[{question_index}].correct") == "true"
            question["boolean_answer"] = {"answer": answer}

        if question_type == "short_answer":
            question["accepted_answer"] = extract_question_answers(
                query_dict, base_key=f"{base_name}[{question_index}].accepted_answers"
            )
        questions.append(question)
        question_index += 1
    return questions


def extract_question_options(question_type, query_dict, base_key):
    option_index = 0
    options = []
    correct_indexes = []
    if question_type == "multiple_choice":
        correct_index = 0
        while True:
            if f"{base_key}.correct[{correct_index}]" not in query_dict:
                break

            correct_indexes.append(
                query_dict.get(f"{base_key}.correct[{correct_index}]")
            )
            correct_index += 1

    while True:
        if f"{base_key}.options[{option_index}]" not in query_dict:
            break

        if question_type == "multiple_choice":
            if str(option_index) in correct_indexes:
                is_correct = True
            else:
                is_correct = False

        elif question_type == "single_choice":
            is_correct = query_dict.get(f"{base_key}.correct") == str(option_index)

        options.append(
            {
                "text": query_dict.get(f"{base_key}.options[{option_index}]"),
                "is_correct": is_correct,
            }
        )
        option_index += 1

    return options


def extract_question_answers(query_dict, base_key):
    answer_index = 0
    answers = []
    while True:
        if f"{base_key}[{answer_index}]" not in query_dict:
            break

        answers.append({"answer": query_dict.get(f"{base_key}[{answer_index}]")})

        answer_index += 1

    return answers


def extract_assignment_content(query_dict, section_index, lesson_index):
    base_name = f"sections[{section_index}].lessons[{lesson_index}].content"

    assignment = {
        "instructions": query_dict.get(f"{base_name}.instructions"),
        "max_score": query_dict.get(f"{base_name}.maxScore"),
        "allow_late_submission": query_dict.get(f"{base_name}.allowLateSubmission"),
        "max_attempts": query_dict.get(f"{base_name}.maxAttempts"),
        "accepted_file_types": query_dict.get(f"{base_name}.acceptedFileTypes"),
        "max_file_size_mb": query_dict.get(f"{base_name}.maxFileSizeMb"),
    }
    due_date = query_dict.get(f"{base_name}.dueDate")

    if due_date != "null":
        assignment["due_date"] = due_date
    return assignment
