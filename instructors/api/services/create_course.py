from datetime import timedelta

from django.db import transaction

from assessments.models import (
    AcceptedAnswer,
    Assignment,
    BooleanAnswer,
    Choice,
    Question,
    QuizContent,
)
from courses.models import (
    Course,
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


class CourseService:
    def __init__(self, instructor):
        self.instructor = instructor

    @transaction.atomic
    def create(self, data):
        course = self._create_course(data)
        self._add_tags(course, data)
        self._create_sections(course, data["sections"])
        self._create_course_attachments(course, data["attachments"])
        self.create_features(course, data)
        self._create_target_audiences(course, data)
        self._create_prerequisites(course, data)
        self._create_outcomes(course, data)

        return course

    def _create_course(self, data):
        category = self._get_category_object(data)

        course = Course.objects.create(
            owner=self.instructor,
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            short_description=data.get("short_description", ""),
            description=data.get("description", ""),
            thumbnail=data.get("thumbnail"),
            promotional_video=data.get("promotional_video", ""),
            course_trailer=data.get("course_trailer", ""),
            language=data.get("language", Course.LANGUAGE.ENGLISH),
            level=data.get("level", Course.Level.ALL_LEVELS),
            visibility=data.get("visibility", Course.Visibility.PUBLIC),
            category=category,
            duration=data.get("duration"),
            price_type=data.get("price_type", Course.PriceType.FREE),
            price=data.get("price"),
            price_discount=data.get("price_discount", 0),
            version=data.get("version", "1.0.0"),
            version_note=data.get("version_note", ""),
            seo_title=data.get("seo_title", ""),
            seo_description=data.get("seo_description", ""),
        )

        return course

    def _create_course_attachments(self, course, attachments):
        for attachment in attachments:
            Attachment.objects.create(course=course, file=attachment["file"])

    def _get_category_object(self, data):
        category = data.get("category", "")
        print("data", data)
        return category

    def _add_tags(self, course, data):
        tags_list = []
        for tag_dict in data.get("tags", []):
            tag, _ = Tag.objects.get_or_create(name=tag_dict["name"])
            tags_list.append(tag)
        course.tags.add(*tags_list)

    def _create_sections(self, course, sections):
        for section_order, section_data in enumerate(sections, start=1):
            section = Section.objects.create(
                course=course,
                title=section_data["title"],
                description=section_data["description"],
                order=section_order,
                duration=section_data["duration"],
            )

            self._create_lessons(section, section_data["lessons"])

    def _create_lessons(self, section, lessons):
        for lesson_order, lesson_data in enumerate(lessons, start=1):
            lesson = Lesson.objects.create(
                section=section,
                title=lesson_data["title"],
                description=lesson_data["description"],
                order=lesson_order,
                duration=timedelta(minutes=lesson_data["duration"]),
                is_published=lesson_data["is_published"],
                is_preview=lesson_data["is_preview"],
            )
            self._create_lesson_completion_criteria(
                lesson=lesson, completion_criteria=lesson_data["completion_criteria"]
            )
            self._create_lesson_content(
                lesson=lesson,
                content=lesson_data["content"],
            )

    def _create_lesson_completion_criteria(self, lesson, completion_criteria):
        LessonCompletionCriteria.objects.create(
            lesson=lesson,
            criteria_type=completion_criteria["criteria_type"],
            video_watch_percentage=completion_criteria["video_watch_percentage"],
            quiz_passing_score=completion_criteria["quiz_passing_score"],
        )

    def _create_lesson_content(self, lesson, content):
        content_type = content["content_type"]
        lesson_content = LessonContent.objects.create(
            lesson=lesson,
            title=content.get("title", lesson.title),
            content_type=content_type,
            order=0,
        )

        self._create_lesson_content_attachments(lesson, lesson_content, content)
        if content_type == "file":
            self._create_file_content(lesson_content, content["file"])
        elif content_type == "article":
            self._create_article_content(lesson_content, content["article"])
        elif content_type == "video":
            self._create_video_content(lesson_content, content["video"])
        elif content_type == "quiz":
            self._create_quiz_content(lesson_content, content["quiz"])

        elif content_type == "assignment":
            self._create_assignment_content(lesson_content, content["assignment"])

    def _create_lesson_content_attachments(self, lesson, lesson_content, content):
        for attachment in content.get("attachments", []):
            Attachment.objects.create(
                course=lesson.section.course,
                lesson_content=lesson_content,
                file=attachment.get("file"),
            )

    def _create_file_content(self, lesson_content, file_content):
        FileContent.objects.create(
            content=lesson_content,
            file=file_content.get("file"),
            file_url=file_content.get("file_url"),
        )

    def _create_article_content(self, lesson_content, article_content):
        ArticleContent.objects.create(
            content=lesson_content, body=article_content["body"]
        )

    def _create_video_content(self, lesson_content, video_content):
        source = "file"
        if video_content["external_url"] != "":
            source = "url"
        print(video_content)
        video_content_obj = VideoContent.objects.create(
            content=lesson_content,
            source=source,
            video_file=video_content.get("video_file"),
            external_url=video_content.get("external_url", ""),
            text=video_content.get("text", ""),
            transcript=video_content.get("transcript"),
        )

        self._create_video_captions(video_content_obj, video_content)

    def _create_video_captions(self, video_content_obj, video_content):
        for caption_content in video_content["captions"]:
            VideoCaption.objects.create(
                video=video_content_obj,
                language=caption_content.get("language"),
                label=caption_content.get("label"),
                file=caption_content.get("file"),
                file_format=caption_content.get("file_format"),
                is_default=caption_content.get("is_default"),
            )

    def _create_quiz_content(self, lesson_content, quiz_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            instructions=quiz_content.get("instructions"),
            passing_score=quiz_content.get("passing_score"),
            time_limit=quiz_content.get("time_limit"),
            max_attempts=quiz_content.get("max_attempts"),
            shuffle_questions=quiz_content.get("shuffle_questions"),
            shuffle_choices=quiz_content.get("shuffle_choices"),
            show_correct_answers=quiz_content.get("show_correct_answers"),
        )

        self._create_quiz_questions(quiz, quiz_content.get("questions"))

    def _create_quiz_questions(self, quiz, question_contents):
        for question_index, question_content in enumerate(question_contents, start=1):
            question_type = question_content["question_type"]

            question = Question.objects.create(
                quiz=quiz,
                text=question_content.get("text"),
                question_type=question_content.get("question_type"),
                difficulty=question_content.get("difficulty"),
                points=question_content.get("points"),
                explanation=question_content.get("explanation"),
                is_required=question_content.get("is_required"),
                estimated_time=question_content.get("estimated_time"),
                order=question_index,
            )

            if question_type in ["single_choice", "multiple_choice"]:
                self._create_question_options(question, question_content["choices"])
            elif question_type == "true_false":
                self._create_boolean_answer(
                    question, question_content["boolean_answer"]
                )

            elif question_type == "short_answer":
                self._create_short_answer(
                    question, question_content["accepted_answers"]
                )

    def _create_question_options(self, question, option_contents):
        for option_index, option_content in enumerate(option_contents, start=1):
            Choice.objects.create(
                question=question,
                text=option_content["text"],
                is_correct=option_content["is_correct"],
                order=option_index,
            )

    def _create_boolean_answer(self, question, boolean_answer):
        BooleanAnswer.objects.create(question=question, answer=boolean_answer["answer"])

    def _create_short_answer(self, question, accepted_answers):
        for accepted_answer in accepted_answers:
            AcceptedAnswer.objects.create(
                question=question, answer=accepted_answer["answer"]
            )

    def _create_assignment_content(self, lesson_content, assignment_content):
        Assignment.objects.create(
            content=lesson_content,
            instructions=assignment_content.get("instructions"),
            passing_score=assignment_content.get("passing_score"),
            max_score=assignment_content.get("max_score"),
            due_date=assignment_content.get("due_date"),
            allow_late_submission=assignment_content.get("allow_late_submission"),
            max_attempts=assignment_content.get("max_attempts"),
            accepted_file_types=assignment_content.get("accepted_file_types"),
            max_file_size_mb=assignment_content.get("max_file_size_mb"),
        )

    def create_features(self, course, data):
        for _index, feature in enumerate(data.get("features", [])):
            CourseFeature.objects.create(
                course=course, icon=feature["icon"], text=feature["text"]
            )

    def _create_target_audiences(self, course, data):
        for index, target_audience_dict in enumerate(data.get("target_audiences", [])):
            TargetAudience.objects.create(
                course=course,
                description=target_audience_dict.get("description"),
                order=index,
            )

    def _create_prerequisites(self, course, data):
        for index, prerequisite_dict in enumerate(data.get("prerequisites", [])):
            Prerequisite.objects.create(
                course=course, description=prerequisite_dict["description"], order=index
            )

    def _create_outcomes(self, course, data):
        for _index, outcome_dict in enumerate(data.get("learning_outcomes", [])):
            LearningOutcome.objects.get_or_create(
                course=course, description=outcome_dict["description"]
            )
