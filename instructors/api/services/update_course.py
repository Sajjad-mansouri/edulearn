from django.db import transaction
from rest_framework.exceptions import ValidationError

from assessments.models import (
    AcceptedAnswer,
    Assignment,
    BooleanAnswer,
    Choice,
    Question,
    QuizContent,
)
from courses.models import (
    CourseFeature,
    LearningOutcome,
    Prerequisite,
    Tag,
    TargetAudience,
)
from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonCompletionCriteria,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)


class CourseUpdateService:
    def __init__(self, course, deleted_ids_dict):
        self.course = course
        self.instructor = course.owner
        self.deleted_ids_dict = deleted_ids_dict

    @transaction.atomic
    def update(self, data):
        """Update course with all related data."""

        course = self._update_course(data)
        self._update_features(course, data)
        self._update_outcomes(course, data)
        self._update_prerequisites(course, data)
        self._update_target_audiences(course, data)

        self._update_tags(course, data)

        self._update_sections(course, data.get("sections", []))

        self._update_course_attachments(course, data.get("attachments", []))
        return course

    def _update_course(self, data):
        """Update course main fields."""
        category = self._get_category_object(data)

        # Update only provided fields
        print("data in _update course:", data)
        field_mapping = {
            "title": data.get("title", self.course.title),
            "subtitle": data.get("subtitle", self.course.subtitle),
            "short_description": data.get(
                "short_description", self.course.short_description
            ),
            "description": data.get("description", self.course.description),
            "thumbnail": data.get("thumbnail", self.course.thumbnail),
            "promotional_video": data.get(
                "promotional_video", self.course.promotional_video
            ),
            "course_trailer": data.get("course_trailer", self.course.course_trailer),
            "language": data.get("language", self.course.language),
            "level": data.get("level", self.course.level),
            "visibility": data.get("visibility", self.course.visibility),
            "category": category,
            "duration": data.get("duration", self.course.duration),
            "price_type": data.get("price_type", self.course.price_type),
            "price": data.get("price", self.course.price),
            "price_discount": data.get("price_discount", self.course.price_discount),
            "version": data.get("version", self.course.version),
            "version_note": data.get("version_note", self.course.version_note),
            "seo_title": data.get("seo_title", self.course.seo_title),
            "seo_description": data.get("seo_description", self.course.seo_description),
        }

        for field, value in field_mapping.items():
            setattr(self.course, field, value)

        self.course.save()
        return self.course

    def _update_features(self, course, data):
        CourseFeature.objects.filter(course=course).delete()
        for _index, feature in enumerate(data.get("features", [])):
            CourseFeature.objects.create(
                course=course, icon=feature["icon"], text=feature["text"]
            )

    def _update_outcomes(self, course, data):
        """Update course outcomes."""

        outcomes = self.deleted_ids_dict.get("outcomes", [])
        LearningOutcome.objects.filter(id__in=outcomes).delete()
        for _index, outcome_dict in enumerate(data.get("learning_outcomes", [])):
            outcome, _ = LearningOutcome.objects.get_or_create(
                course=course, description=outcome_dict["description"]
            )

    def _update_prerequisites(self, course, data):
        """Update course prerequisite."""

        prerequisites = self.deleted_ids_dict.get("prerequisites", [])
        Prerequisite.objects.filter(id__in=prerequisites).delete()

        for index, prerequisite_dict in enumerate(data.get("prerequisites", [])):
            prerequisite_id = prerequisite_dict.get("id")
            description = prerequisite_dict["description"]
            if prerequisite_id:
                try:
                    prerequisite = Prerequisite.objects.get(
                        course=course, id=prerequisite_id
                    )
                    prerequisite.description = description
                    prerequisite.order = index
                    prerequisite.save()
                except Prerequisite.DoesNotExist:
                    raise ValidationError(
                        f"Prerequisite with id {prerequisite_id} not found"
                    ) from None

            else:
                prerequisite = Prerequisite.objects.create(
                    course=course, description=description, order=index
                )

    def _update_target_audiences(self, course, data):
        """Update course target_audience."""

        target_audiences = self.deleted_ids_dict.get("target_audiences", [])
        TargetAudience.objects.filter(id__in=target_audiences).delete()
        for index, target_audience_dict in enumerate(data.get("target_audiences", [])):
            target_audiences_id = target_audience_dict.get("id")
            description = target_audience_dict.get("description")

            if target_audiences_id:
                try:
                    target_audience = TargetAudience.objects.get(
                        course=course, id=target_audiences_id
                    )
                    target_audience.description = description
                    target_audience.order = index
                    target_audience.save()
                except TargetAudience.DoesNotExist:
                    raise ValidationError(
                        f"TargetAudience with id {target_audiences_id} not found"
                    ) from None

            else:
                target_audience = TargetAudience.objects.create(
                    course=course, description=description, order=index
                )

    def _update_tags(self, course, data):
        """Update course tags."""
        if "tags" in data:
            tags_list = []
            for tag_dict in data.get("tags", []):
                tag, _ = Tag.objects.get_or_create(name=tag_dict["name"])
                tags_list.append(tag)
            course.tags.set(tags_list)

    def _update_course_attachments(self, course, attachments):
        """Update course attachments."""

        deleted_attachments = self.deleted_ids_dict.get("attachments", [])

        Attachment.objects.filter(id__in=deleted_attachments).delete()

        for attachment in attachments:
            if attachment.get("id"):
                Attachment.objects.filter(id=attachment["id"], course=course).update(
                    file=attachment["file"]
                )
            elif attachment.get("file"):
                Attachment.objects.create(course=course, file=attachment["file"])

    def _update_sections(self, course, sections):
        """Update course sections and their contents."""
        # Delete sections not in the update payload
        print(
            "sections in _update sections",
            sections,
        )
        deleted_sections = self.deleted_ids_dict.get("sections", [])

        Section.objects.filter(id__in=deleted_sections).delete()
        # section_ids = [section.get("id") for section in sections if section.get("id")]
        # Section.objects.filter(course=course).exclude(id__in=section_ids).delete()
        print("sections", sections)
        print("before loop fo sections")
        for section_order, section_data in enumerate(sections, start=1):
            print("**section order", section_order)
            if section_data.get("id"):
                section = self._update_section(section_data, section_order)
            else:
                section = self._create_section(course, section_data, section_order)
            print("_update_lessons")
            self._update_lessons(section, section_data.get("lessons", []))

    def _update_section(self, section_data, order):
        """Update existing section."""

        try:
            section = Section.objects.get(id=section_data["id"], course=self.course)
            section.title = section_data.get("title", section.title)
            section.description = section_data.get("description", section.description)
            section.order = order
            section.duration = section_data.get("duration", section.duration)
            section.save()
            return section
        except Section.DoesNotExist:
            raise ValidationError(
                f"Section with id {section_data['id']} not found"
            ) from None

    def _create_section(self, course, section_data, order):
        """Create new section."""
        return Section.objects.create(
            course=course,
            title=section_data["title"],
            description=section_data.get("description", ""),
            order=order,
            duration=section_data.get("duration"),
        )

    def _update_lessons(self, section, lessons):
        """Update lessons within a section."""
        deleted_lessons = self.deleted_ids_dict.get("lessons", [])
        Lesson.objects.filter(id__in=deleted_lessons).delete()

        for lesson_order, lesson_data in enumerate(lessons, start=1):
            if lesson_data.get("id"):
                lesson = self._update_lesson(lesson_data, lesson_order)
            else:
                lesson = self._create_lesson(section, lesson_data, lesson_order)

            self._update_lesson_completion_criteria(
                lesson, lesson_data.get("completion_criteria")
            )
            self._update_lesson_content(lesson, lesson_data.get("content", {}))

    def _update_lesson(self, lesson_data, order):
        """Update existing lesson."""
        print("update lesson")

        try:
            lesson = Lesson.objects.get(
                id=lesson_data["id"], section__course=self.course
            )
            lesson.title = lesson_data.get("title", lesson.title)
            lesson.description = lesson_data.get("description", lesson.description)
            lesson.order = order
            print(lesson_data.get("duration"), lesson_data)

            lesson.duration = lesson_data.get("duration", lesson.duration)
            lesson.is_published = lesson_data.get("is_published", lesson.is_published)
            lesson.is_preview = lesson_data.get("is_preview", lesson.is_preview)
            lesson.save()
            return lesson
        except Lesson.DoesNotExist:
            raise ValidationError(
                f"Lesson with id {lesson_data['id']} not found"
            ) from None

    def _create_lesson(self, section, lesson_data, order):
        """Create new lesson."""
        return Lesson.objects.create(
            section=section,
            title=lesson_data["title"],
            description=lesson_data.get("description", ""),
            order=order,
            duration=lesson_data.get("duration"),
            is_published=lesson_data.get("is_published", False),
            is_preview=lesson_data.get("is_preview", False),
        )

    def _update_lesson_completion_criteria(self, lesson, completion_criteria):
        """Update lesson completion criteria."""
        if not completion_criteria:
            return

        try:
            criteria = LessonCompletionCriteria.objects.get(lesson=lesson)
            criteria.criteria_type = completion_criteria.get(
                "criteria_type", criteria.criteria_type
            )
            criteria.video_watch_percentage = completion_criteria.get(
                "video_watch_percentage", criteria.video_watch_percentage
            )
            criteria.quiz_passing_score = completion_criteria.get(
                "quiz_passing_score", criteria.quiz_passing_score
            )
            criteria.save()
        except LessonCompletionCriteria.DoesNotExist:
            LessonCompletionCriteria.objects.create(
                lesson=lesson,
                criteria_type=completion_criteria["criteria_type"],
                video_watch_percentage=completion_criteria.get(
                    "video_watch_percentage"
                ),
                quiz_passing_score=completion_criteria.get("quiz_passing_score"),
            )

    def _update_lesson_content(self, lesson, content):
        """Update lesson content items."""
        if content.get("id"):
            lesson_content = self._update_lesson_content_item(content)
        else:
            lesson_content = self._create_lesson_content(lesson, content)

        self._update_specific_content(lesson_content, content)

    def _update_lesson_content_item(self, content_data, order=0):
        """Update existing lesson content."""
        try:
            lesson_content = LessonContent.objects.get(
                id=content_data["id"], lesson__section__course=self.course
            )
            should_remove_specific_content = False
            pre_lesson_content_type = lesson_content.content_type
            if pre_lesson_content_type != content_data.get("content_type"):
                should_remove_specific_content = True

            lesson_content.content_type = content_data.get(
                "content_type", lesson_content.content_type
            )
            lesson_content.order = order
            lesson_content.save()

            # Remove old specific content
            if should_remove_specific_content:
                self._delete_specific_content(lesson_content, pre_lesson_content_type)

            return lesson_content
        except LessonContent.DoesNotExist:
            raise ValidationError(
                f"Lesson content with id {content_data['id']} not found"
            ) from None

    def _create_lesson_content(self, lesson, content_data, order):
        """Create new lesson content."""

        return LessonContent.objects.create(
            lesson=lesson, content_type=content_data["content_type"], order=order
        )

    def _delete_specific_content(self, lesson_content, pre_lesson_content_type):
        """Delete specific content based on type."""
        content_type_models = {
            "file": FileContent,
            "article": ArticleContent,
            "video": VideoContent,
            "quiz": QuizContent,
            "assignment": Assignment,
        }
        model = content_type_models.get(pre_lesson_content_type)
        if model:
            model.objects.filter(content=lesson_content).delete()

    def _update_specific_content(self, lesson_content, content_data):
        """Update or create specific content."""
        content_type = content_data.get("content_type", lesson_content.content_type)

        self._update_lesson_content_attachments(
            lesson_content, content_data.get("attachments", [])
        )

        if content_type == "file":
            self._update_file_content(lesson_content, content_data.get("file", {}))
        elif content_type == "article":
            self._update_article_content(
                lesson_content, content_data.get("article", {})
            )
        elif content_type == "video":
            self._update_video_content(lesson_content, content_data.get("video", {}))
        elif content_type == "quiz":
            self._update_quiz_content(lesson_content, content_data.get("quiz", {}))
        elif content_type == "assignment":
            self._update_assignment_content(
                lesson_content, content_data.get("assignment", {})
            )

    def _update_file_content(self, lesson_content, file_content):
        """Update file content."""
        if not file_content:
            return

        try:
            file_obj = FileContent.objects.get(content=lesson_content)
            file_obj.file = file_content.get("file", file_obj.file)
            file_obj.file_url = file_content.get("file_url", file_obj.file_url)
            file_obj.save()
        except FileContent.DoesNotExist:
            FileContent.objects.create(
                content=lesson_content,
                file=file_content.get("file"),
                file_url=file_content.get("file_url", ""),
            )

    def _update_article_content(self, lesson_content, article_content):
        """Update article content."""
        if not article_content:
            return

        try:
            article = ArticleContent.objects.get(content=lesson_content)
            article.body = article_content.get("body", article.body)
            article.save()
        except ArticleContent.DoesNotExist:
            ArticleContent.objects.create(
                content=lesson_content,
                body=article_content.get("body", ""),
            )

    def _update_video_content(self, lesson_content, video_content):
        """Update video content."""

        if not video_content:
            return

        source = "file"
        if video_content.get("external_url"):
            source = "url"
        try:
            video = VideoContent.objects.get(content=lesson_content)
            video.source = source
            video.video_file = video_content.get("video_file", video.video_file)
            video.external_url = video_content.get("external_url", video.external_url)
            video.text = video_content.get("text", video.text)
            video.duration = video_content.get("duration", video.duration)
            video.transcript = video_content.get("transcript", video.transcript)
            video.save()

            self._update_video_captions(video, video_content.get("captions", []))
        except VideoContent.DoesNotExist:
            video = VideoContent.objects.create(
                content=lesson_content,
                source=source,
                video_file=video_content.get("video_file"),
                external_url=video_content.get("external_url", ""),
                text=video_content.get("text", ""),
                duration=video_content.get("duration"),
                transcript=video_content.get("transcript", ""),
            )

            self._create_video_captions(video, video_content.get("captions", []))

    def _update_video_captions(self, video, captions):
        """Update video captions."""
        deleted_captions_ids = self.deleted_ids_dict["captions"]
        # caption_ids = [caption.get("id") for caption in captions if caption.get("id")]
        VideoCaption.objects.filter(id__in=deleted_captions_ids).delete()

        for caption_data in captions:
            if caption_data.get("id"):
                VideoCaption.objects.filter(id=caption_data["id"], video=video).update(
                    language=caption_data.get("language"),
                    label=caption_data.get("label"),
                    file=caption_data.get("file"),
                    file_format=caption_data.get("file_format"),
                    is_default=caption_data.get("is_default", False),
                )
            else:
                VideoCaption.objects.create(
                    video=video,
                    language=caption_data["language"],
                    label=caption_data.get("label", ""),
                    file=caption_data["file"],
                    file_format=caption_data.get("file_format", "vtt"),
                    is_default=caption_data.get("is_default", False),
                )

    def _update_quiz_content(self, lesson_content, quiz_content):
        """Update quiz content."""
        if not quiz_content:
            return

        try:
            quiz = QuizContent.objects.get(content=lesson_content)
            quiz.instructions = quiz_content.get("instructions", quiz.instructions)
            quiz.passing_score = quiz_content.get("passing_score", quiz.passing_score)
            quiz.time_limit = quiz_content.get("time_limit", quiz.time_limit)
            quiz.max_attempts = quiz_content.get("max_attempts", quiz.max_attempts)
            quiz.shuffle_questions = quiz_content.get(
                "shuffle_questions", quiz.shuffle_questions
            )
            quiz.shuffle_choices = quiz_content.get(
                "shuffle_choices", quiz.shuffle_choices
            )
            quiz.show_correct_answers = quiz_content.get(
                "show_correct_answers", quiz.show_correct_answers
            )
            quiz.save()

            self._update_quiz_questions(quiz, quiz_content.get("questions", []))
        except QuizContent.DoesNotExist:
            quiz = QuizContent.objects.create(
                content=lesson_content,
                instructions=quiz_content.get("instructions", ""),
                passing_score=quiz_content.get("passing_score"),
                time_limit=quiz_content.get("time_limit"),
                max_attempts=quiz_content.get("max_attempts"),
                shuffle_questions=quiz_content.get("shuffle_questions", False),
                shuffle_choices=quiz_content.get("shuffle_choices", False),
                show_correct_answers=quiz_content.get("show_correct_answers", False),
            )
            self._create_quiz_questions(quiz, quiz_content.get("questions", []))

    def _update_quiz_questions(self, quiz, questions):
        """Update quiz questions."""

        question_ids = [q.get("id") for q in questions if q.get("id")]
        Question.objects.filter(quiz=quiz).exclude(id__in=question_ids).delete()

        for question_order, question_data in enumerate(questions, start=1):
            if question_data.get("id"):
                self._update_question(question_data, question_order)
            else:
                self._create_question(quiz, question_data, question_order)

    def _update_question(self, question_data, order):
        """Update existing question."""
        try:
            question = Question.objects.get(
                id=question_data["id"],
                quiz__content__lesson__section__course=self.course,
            )
            question.text = question_data.get("text", question.text)
            question.question_type = question_data.get(
                "question_type", question.question_type
            )
            question.difficulty = question_data.get("difficulty", question.difficulty)
            question.points = question_data.get("points", question.points)
            question.explanation = question_data.get(
                "explanation", question.explanation
            )
            question.is_required = question_data.get(
                "is_required", question.is_required
            )
            question.estimated_time = question_data.get(
                "estimated_time", question.estimated_time
            )
            question.order = order
            question.save()

            # Update question-specific answers
            self._delete_question_answers(question)
            self._create_question_answers(question, question_data)

            return question
        except Question.DoesNotExist:
            raise ValidationError(
                f"Question with id {question_data['id']} not found"
            ) from None

    def _create_question(self, quiz, question_data, order):
        """Create new question."""
        question = Question.objects.create(
            quiz=quiz,
            text=question_data["text"],
            question_type=question_data["question_type"],
            difficulty=question_data.get("difficulty", "medium"),
            points=question_data.get("points", 1),
            explanation=question_data.get("explanation", ""),
            is_required=question_data.get("is_required", True),
            estimated_time=question_data.get("estimated_time"),
            order=order,
        )
        self._create_question_answers(question, question_data)
        return question

    def _delete_question_answers(self, question):
        """Delete all answers for a question."""
        Choice.objects.filter(question=question).delete()
        BooleanAnswer.objects.filter(question=question).delete()
        AcceptedAnswer.objects.filter(question=question).delete()

    def _create_question_answers(self, question, question_data):
        """Create answers based on question type."""
        question_type = question.question_type

        if question_type in ["single_choice", "multiple_choice"]:
            self._create_question_options(question, question_data.get("choices", []))
        elif question_type == "true_false":
            self._create_boolean_answer(
                question, question_data.get("boolean_answer", {})
            )
        elif question_type == "short_answer":
            self._create_short_answer(
                question, question_data.get("accepted_answers", [])
            )

    def _update_assignment_content(self, lesson_content, assignment_content):
        """Update assignment content."""
        if not assignment_content:
            return

        try:
            assignment = Assignment.objects.get(content=lesson_content)
            assignment.instructions = assignment_content.get(
                "instructions", assignment.instructions
            )
            assignment.max_score = assignment_content.get(
                "max_score", assignment.max_score
            )
            assignment.due_date = assignment_content.get(
                "due_date", assignment.due_date
            )
            assignment.allow_late_submission = assignment_content.get(
                "allow_late_submission", assignment.allow_late_submission
            )
            assignment.max_attempts = assignment_content.get(
                "max_attempts", assignment.max_attempts
            )
            assignment.accepted_file_types = assignment_content.get(
                "accepted_file_types", assignment.accepted_file_types
            )
            assignment.max_file_size_mb = assignment_content.get(
                "max_file_size_mb", assignment.max_file_size_mb
            )
            assignment.save()
        except Assignment.DoesNotExist:
            Assignment.objects.create(
                content=lesson_content,
                instructions=assignment_content.get("instructions", ""),
                max_score=assignment_content.get("max_score"),
                due_date=assignment_content.get("due_date"),
                allow_late_submission=assignment_content.get(
                    "allow_late_submission", False
                ),
                max_attempts=assignment_content.get("max_attempts"),
                accepted_file_types=assignment_content.get("accepted_file_types"),
                max_file_size_mb=assignment_content.get("max_file_size_mb"),
            )

    def _get_category_object(self, data):
        """Get category object from data."""
        print(data)
        category = data.get("category")
        return category

    def _update_lesson_content_attachments(self, lesson_content, attachments):
        """Update lesson content attachments."""
        attachment_ids = [att.get("id") for att in attachments if att.get("id")]
        Attachment.objects.filter(lesson_content=lesson_content).exclude(
            id__in=attachment_ids
        ).delete()

        for attachment_data in attachments:
            if attachment_data.get("id"):
                Attachment.objects.filter(
                    id=attachment_data["id"], lesson_content=lesson_content
                ).update(file=attachment_data.get("file"))
            else:
                Attachment.objects.create(
                    course=lesson_content.lesson.section.course,
                    lesson_content=lesson_content,
                    file=attachment_data["file"],
                )

    def _create_question_options(self, question, option_contents):
        """Create choice options for question."""

        for option_index, option_content in enumerate(option_contents, start=1):
            Choice.objects.create(
                question=question,
                text=option_content["text"],
                is_correct=option_content.get("is_correct", False),
                order=option_index,
            )

    def _create_boolean_answer(self, question, boolean_answer):
        """Create boolean answer."""
        if boolean_answer:
            BooleanAnswer.objects.create(
                question=question, answer=boolean_answer.get("answer", True)
            )

    def _create_short_answer(self, question, accepted_answers):
        """Create accepted answers for short answer question."""
        for accepted_answer in accepted_answers:
            AcceptedAnswer.objects.create(
                question=question, answer=accepted_answer["answer"]
            )

    def _create_video_captions(self, video, captions):
        """Create video captions."""
        for caption_data in captions:
            VideoCaption.objects.create(
                video=video,
                language=caption_data["language"],
                label=caption_data.get("label", ""),
                file=caption_data["file"],
                file_format=caption_data.get("file_format", "vtt"),
                is_default=caption_data.get("is_default", False),
            )

    def _create_quiz_questions(self, quiz, questions):
        """Create quiz questions."""
        for question_order, question_data in enumerate(questions, start=1):
            self._create_question(quiz, question_data, question_order)
