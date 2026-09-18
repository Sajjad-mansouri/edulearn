from django.db import transaction
from django.db.models import Avg, Count, Exists, OuterRef, Prefetch, Q, Subquery
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assessments.models import (
    AcceptedAnswer,
    AssignmentSubmission,
    AssignmentSubmissionFile,
    BooleanAnswer,
    Choice,
    Question,
    QuizAnswer,
    QuizAttempt,
    QuizContent,
)
from certificates.models import Certificate
from courses.models import Course, CourseWishlist
from curriculums.models import Attachment, Lesson, LessonContent, Section
from enrollments.models import (
    CourseLessonBookmark,
    Enrollment,
    LessonContentProgress,
    LessonProgress,
    VideoProgress,
    VideoWatchEvent,
)

from .mixins import EnrollmentResolverMixin
from .permissions import IsEnrolled, IsOwner, IsStudent
from .serializers import (
    AssignmentSerializer,
    AssignmentSubmissionFileSerializer,
    AssignmentSubmissionSerializer,
    AttachmentSerializer,
    EnrollmentCourseSerializer,
    QuizSerializer,
    QuizSubmission,
    StudentCourseCertificateSerializer,
    StudentCourseSerializer,
    StudentWishlistSerializer,
)


class CurrentUserEnrollmentStatus(GenericAPIView):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        print("course_id", course_id)
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            enrollment = Enrollment.objects.filter(
                course=course,
                user=request.user,
                status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
            ).first()
            enrollment_id = None
            is_enrolled = False
            if enrollment:
                enrollment_id = enrollment.id
                is_enrolled = True

            return Response(
                {"is_enrolled": is_enrolled, "enrollment_id": enrollment_id}
            )

        return Response({"is_enrolled": False})


class EnrollmentCourseApiView(EnrollmentResolverMixin, RetrieveAPIView):
    serializer_class = EnrollmentCourseSerializer
    permission_classes = [IsOwner | IsEnrolled]

    def get_queryset(self):
        # For a specific course, get all sections with lessons and attachment info
        print("enrollment", self.enrollment)
        if self.enrollment:
            q = Q(id=self.enrollment.course_id)
        else:
            q = Q(owner=self.request.user)
        return (
            Course.objects.filter(q)
            .prefetch_related(
                Prefetch(
                    "sections",
                    queryset=Section.objects.prefetch_related(
                        Prefetch(
                            "lessons",
                            queryset=Lesson.objects.annotate(
                                has_attachments=Exists(
                                    Attachment.objects.filter(
                                        lesson_content__lesson=OuterRef("pk")
                                    )
                                ),
                                attachment_count=Count(
                                    "content__attachments", distinct=True
                                ),
                                type=Subquery(
                                    LessonContent.objects.filter(
                                        lesson=OuterRef("pk"), is_main_content=True
                                    ).values("content_type")[:1]
                                ),
                            ),
                        )
                    ).order_by("order"),
                )
            )
            .annotate(total_lessons=Count("sections__lessons", distinct=True))
        )

    def get_object(self):
        qs = self.get_queryset()
        enrollment_id = self.kwargs.get("enrollment_id")
        course_id = self.kwargs.get("course_id")
        if enrollment_id:
            return get_object_or_404(
                qs, enrollments__id=enrollment_id, enrollments__user=self.request.user
            )
        elif course_id:
            return get_object_or_404(qs, id=course_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["enrollment_id"] = self.kwargs.get("enrollment_id")
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)


class LessonContentApiView(EnrollmentResolverMixin, GenericAPIView):
    lookup_url_kwarg = "lesson_id"
    permission_classes = [IsOwner | IsEnrolled]

    def get(self, request, *args, **kwargs):
        lesson = self.get_object()
        content = get_object_or_404(LessonContent, lesson=lesson, is_main_content=True)

        response_data = self.build_content_response(request, content, lesson)
        return Response(response_data)

    def get_queryset(self):
        if self.enrollment:
            q = Q(section__course=self.enrollment.course)
        else:
            q = Q(section__course__owner=self.request.user)
        return (
            Lesson.objects.filter(q)
            .select_related(
                "section__course",
                "content",
                "content__video",
                "content__article",
                "content__file",
                "content__quiz",
                "content__assignment",
            )
            .prefetch_related("content__attachments")
        )

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.kwargs["lesson_id"])

    def build_content_response(self, request, content, lesson):
        resources = self._get_attachments(content)
        base_data = {
            "id": lesson.id,
            "description": lesson.description,
            "resources": resources,
            "video_progress": {"timestamp": 0},
        }

        handlers = {
            "video": self._handle_video_content,
            "article": self._handle_article_content,
            "file": self._handle_file_content,
            "quiz": self._handle_quiz_content,
            "assignment": self._handle_assignment_content,
        }

        handler = handlers.get(content.content_type)
        if handler:
            base_data.update(handler(request, content, lesson))
        else:
            base_data["error"] = f"Unsupported content type: {content.content_type}"

        return base_data

    def _handle_video_content(self, request, content, lesson):
        data = {
            "videoUrl": self._get_file_url(request, content.video.video_file),
        }
        if self.enrollment:
            video_progress = self._get_or_create_video_progress(request.user, content)
            data["video_progress"] = {
                "timestamp": video_progress.watched_seconds or 0,
            }
        return data

    def _handle_article_content(self, request, content, lesson):
        return {
            "articleContent": content.article.body,
        }

    def _handle_file_content(self, request, content, lesson):
        return {
            "fileUrl": self._get_file_url(request, content.file.file),
            "fileName": content.file.file.name,
            "fileSize": content.file.file.size,
        }

    def _handle_quiz_content(self, request, content, lesson):
        # Don't expose answers in GET request!
        serializer = QuizSerializer(
            instance=content.quiz,
        )
        return {"quizData": serializer.data}

    def _handle_assignment_content(self, request, content, lesson):
        serializer = AssignmentSerializer(
            instance=content.assignment, context={"request": request}
        )
        return {"assignmentData": serializer.data}

    def _get_or_create_video_progress(self, user, content):
        try:
            vp = VideoProgress.objects.select_related("lesson_content_progress").get(
                lesson_content_progress__enrollment=self.enrollment,
                lesson_content_progress__content=content,
            )
            print(
                "FOUND VideoProgress id =",
                vp.id,
                "watched_seconds =",
                vp.watched_seconds,
            )
            return vp
        except VideoProgress.DoesNotExist:
            with transaction.atomic():
                content_progress, created = LessonContentProgress.objects.get_or_create(
                    enrollment=self.enrollment,
                    content=content,
                )

                if created:
                    content_progress.status = LessonContentProgress.Status.IN_PROGRESS
                    content_progress.save(update_fields=["status"])
                return VideoProgress.objects.create(
                    lesson_content_progress=content_progress,
                    watched_seconds=0,
                )

    def _get_file_url(self, request, file_field):
        if hasattr(file_field, "url"):
            return request.build_absolute_uri(file_field.url)
        return None

    def _get_attachments(self, content):
        attachments = content.attachments
        attachment_serializer = AttachmentSerializer(instance=attachments, many=True)
        return attachment_serializer.data


class LessonCompletion(EnrollmentResolverMixin, GenericAPIView):
    lookup_url_kwarg = "lesson_id"
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        instance = self.get_object()
        qs = self.get_queryset()
        print("instance in lessoncomletion", instance)
        content = instance.content
        lesson_content_progress, _created = LessonContentProgress.objects.get_or_create(
            content=content, enrollment=self.enrollment
        )
        lesson_content_progress.mark_completed()
        completed_lessons = list(
            qs.filter(
                progress_records__status=LessonProgress.Status.COMPLETED
            ).values_list("id", flat=True)
        )
        completed_count = len(completed_lessons)
        total_lessons = qs.count()
        return Response(
            {
                "success": True,
                "completedLessons": completed_lessons,
                "completedCount": completed_count,
                "totalLessons": total_lessons,
            }
        )

    def get_queryset(self):
        return Lesson.objects.filter(section__course__enrollments=self.enrollment)


class EnrollmentProgress(EnrollmentResolverMixin, RetrieveAPIView):
    """
    enrollmentId: enrollmentId,
    overallProgress: 0,
    completedLessons: [],
    completedCount: 0,
    totalLessons: 12,
    bookmarkedLessons: []

    """

    lookup_url_kwarg = "enrollment_id"
    permission_classes = [IsEnrolled]

    def get(self, request, enrollment_id):
        enrollment = self.get_object()
        completed_lessons = self.get_completed_lessons(enrollment)
        completed_count = len(completed_lessons)
        bookmarked_lessons = self.get_bookmarked_lessons(enrollment)
        data = {
            "enrollmentId": enrollment_id,
            "overallProgress": enrollment.progress,
            "completedLessons": completed_lessons,
            "completedCount": completed_count,
            "totalLessons": enrollment.total_lessons,
            "bookmarkedLessons": bookmarked_lessons,
        }
        return Response(data)

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).annotate(
            total_lessons=Count("course__sections__lessons", distinct=True)
        )

    def get_completed_lessons(self, enrollment):
        return Lesson.objects.filter(
            section__course__enrollments__id=enrollment.id,
            progress_records__status=LessonProgress.Status.COMPLETED,
        ).values_list("id", flat=True)

    def get_bookmarked_lessons(self, enrollment):
        return Lesson.objects.filter(bookmarks__enrollment=enrollment).values_list(
            "id", flat=True
        )


class LessonVideoProgressApiView(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        # Validate input
        timestamp = request.data.get("timestamp")
        if timestamp is None or not isinstance(timestamp, int | float) or timestamp < 0:
            return Response({"error": "Valid timestamp required"}, status=400)

        # Get content using self.enrollment
        lesson_content = get_object_or_404(
            LessonContent,
            lesson__id=lesson_id,
            lesson__section__course=self.enrollment.course,
            content_type=LessonContent.Type.VIDEO,
        )

        # Single query - update_or_create using self.enrollment
        try:
            video_progress = VideoProgress.objects.get(
                lesson_content_progress__enrollment=self.enrollment,
                lesson_content_progress__content=lesson_content,
            )
            instance_timestamp = video_progress.watched_seconds
            video_progress.watched_seconds = max(timestamp, instance_timestamp)
            video_progress.save(update_fields=["watched_seconds"])
        except VideoProgress.DoesNotExist:
            VideoProgress.objects.create(
                lesson_content_progress__enrollment=self.enrollment,
                lesson_content_progress__content=lesson_content,
                watched_seconds=timestamp,
            )

        VideoWatchEvent.objects.create(
            video_progress=video_progress, watched_seconds=timestamp
        )
        return Response({"success": True})


class LessonBookmarkApiView(EnrollmentResolverMixin, GenericAPIView):
    """
    Toggle bookmark for a lesson.
    Returns:
        - success: bool
        - bookmarked: bool (True if bookmarked, False if removed)
        - bookmarkedLessons: list of lesson IDs
        - message: string
    """

    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        # Use self.enrollment from mixin
        enrollment = self.enrollment

        # Verify lesson belongs to the enrolled course
        lesson = get_object_or_404(
            Lesson, id=lesson_id, section__course=enrollment.course
        )

        # Toggle bookmark
        bookmark, created = CourseLessonBookmark.objects.get_or_create(
            enrollment=enrollment, lesson=lesson
        )

        if not created:
            bookmark.delete()

        # Get all bookmarked lessons for this enrollment
        bookmarked_lessons = Lesson.objects.filter(
            bookmarks__enrollment=enrollment
        ).values_list("id", flat=True)

        data = {
            "success": True,
            "bookmarked": created,
            "bookmarkedLessons": list(bookmarked_lessons),
            "message": "Lesson bookmarked" if created else "Bookmark removed",
        }
        return Response(data)


class QuizSubmitApiViewv1(EnrollmentResolverMixin, GenericAPIView):
    """
    get these data:
    {'answers':
    [{'questionId': 22, 'questionType': 'single_choice', 'selectedValue': '2'},
    {'questionId': 23, 'questionType': 'short_answer', 'textAnswer': 'this is answer'},
    {'questionId': 24, 'questionType': 'true_false', 'boolValue': 'True'},
    {'questionId': 25, 'questionType': 'multiple_choice', 'selectedValues': ['str()', 'doble quetation']}
    ]}

    return these data:
        success: true,
        score: correctCount,
        totalQuestions: totalQuestions,
        percentage: percentage,
        passed: passed,
        passScore: passScore,

        max_attempts: maxAttempts,
        attempts_used: newAttemptNumber,
        attempts_remaining: Math.max(0, maxAttempts - newAttemptNumber),
        best_score: bestScore,

        questionResults: questionResults,
            questionId: answer.questionId,
            isCorrect: isCorrect,
            correctAnswer: correctAnswer,
            explanation: isCorrect ? 'Correct! Well done.' : 'Review the material and try again.',
            userAnswer: userAnswerDisplay,
            questionType: answer.questionType

        includeCorrectAnswers: includeCorrectAnswers,

        lessonCompleted: lessonCompleted,
        completedLessons: lessonCompleted ? completedLessons : null,
        completedCount: lessonCompleted ? completedCount : null,
        overallProgress: lessonCompleted ? overallProgress : null,

        message: passed ? `Passed with ${percentage}%!` : `Scored ${percentage}%. Need ${passScore}% to pass.`


    """

    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        quiz = QuizContent.objects.filter(content__lesson=lesson)[0]
        attempt_number = 0
        quiz_attempts = QuizAttempt.objects.filter(
            enrollment=self.enrollment, quiz=quiz
        )
        if quiz_attempts.exists():
            attempt_number = (
                QuizAttempt.objects.filter(enrollment=self.enrollment, quiz=quiz)
                .order_by("-attempt_number")[0]
                .attempt_number
            )

        if attempt_number < quiz.max_attempts:
            attempt_number += 1
            serializer = QuizSubmission(data=request.data.get("answers", []), many=True)

            quiz_attempt = QuizAttempt.objects.create(
                enrollment=self.enrollment, quiz=quiz, attempt_number=attempt_number
            )
            question_results = []
            results = []
            for answer in serializer.validated_data:
                question_result = {}
                question = get_object_or_404(Question, id=answer.get("questionId"))
                question_type = answer.get("questionType")
                if question_type in ["single_choice", "multiple_choice"]:
                    user_answer = answer.get("selectedValues")
                    quiz_answer = QuizAnswer.objects.create(
                        attempt=quiz_attempt, question=question
                    )
                    choices = Choice.objects.filter(id__in=user_answer)
                    quiz_answer.selected_choices.set(choices)
                    question_result, isCorrect = self.get_question_result(
                        question, question_type, choices, user_answer
                    )

                elif answer.get("questionType") == "short_answer":
                    user_answer = answer.get("textAnswer")
                    quiz_answer = QuizAnswer.objects.create(
                        attempt=quiz_attempt, question=question, text_answer=user_answer
                    )
                    question_result, isCorrect = self.get_question_result(
                        question, question_type, choices, user_answer
                    )

                elif answer.get("questionType") == "true_false":
                    user_answer = answer.get("boolValue")
                    quiz_answer = QuizAnswer.objects.create(
                        attempt=quiz_attempt, question=question, bool_answer=user_answer
                    )
                    question_result, isCorrect = self.get_question_result(
                        question, question_type, choices, user_answer
                    )

                results.append(isCorrect)
                question_results.append(question_result)
            data = self.prepare_result(
                self.enrollment, lesson, quiz, question_results, results
            )
        else:
            max_attempts, attempts_used, attempts_remaining, best_score = (
                self.get_attempts_data(quiz, quiz_attempts)
            )
            data = {
                "success": False,
                "max_attempts": max_attempts,
                "attempts_used": attempts_used,
                "attempts_remaining": attempts_remaining,
                "best_score": best_score,
            }
        return Response(data)

    def prepare_result(self, enrollment, lesson, quiz, question_results, results):
        total_questions = len(results)
        pass_score = quiz.passing_score
        include_correct_answers = quiz.show_correct_answers
        score = results.count(True)
        percentage = (score / total_questions) * 100
        passed = True if percentage >= pass_score else False
        content = lesson.content
        lesson_content_progress, _created = LessonContentProgress.objects.get_or_create(
            content=content, enrollment=enrollment
        )
        if passed:
            lessonCompleted = self.mark_lesson_content_completed(
                lesson_content_progress
            )
        else:
            lessonCompleted = False
        completedLessons, completedCount, total_lessons = self.get_lesson_progress_data(
            enrollment
        )
        quiz_attempts = QuizAttempt.objects.filter(enrollment=enrollment, quiz=quiz)
        max_attempts, attempts_used, attempts_remaining, best_score = (
            self.get_attempts_data(quiz, quiz_attempts)
        )

        question_results = question_results
        success = True
        return {
            "success": success,
            "score": score,
            "totalQuestions": total_questions,
            "percentage": percentage,
            "passed": passed,
            "passScore": pass_score,
            "max_attempts": max_attempts,
            "attempts_used": attempts_used,
            "attempts_remaining": attempts_remaining,
            "best_score": best_score,
            "questionResults": question_results if include_correct_answers else [],
            "includeCorrectAnswers": include_correct_answers,
            "lessonCompleted": lessonCompleted,
            "completedLessons": completedLessons,
            "completedCount": completedCount,
            "total_lessons": total_lessons,
            "overallProgress": enrollment.course.progress,
            "message": f"Passed with ${percentage}%!"
            if passed
            else f"Scored ${percentage}%. Need ${pass_score}% to pass.",
        }

    def mark_lesson_content_completed(self, lesson_content_progress):
        lesson_content_progress.mark_completed()
        lessonCompleted = True
        return lessonCompleted

    def get_lesson_progress_data(self, enrollment):
        lessons = Lesson.objects.filter(section__course__enrollments__id=enrollment.id)
        completed_lessons = lessons.filter(
            progress_records__status=LessonProgress.Status.COMPLETED
        ).values_list("id", flat=True)
        completed_count = completed_lessons.count()
        total_lessons = lessons.count()
        return completed_lessons, completed_count, total_lessons

    def get_attempts_data(self, quiz, quiz_attempts):
        max_attempts = quiz.maxAttempts
        attempts_used = quiz_attempts.order_by("-attempt_number")[0].attempt_number
        attempts_remaining = max_attempts - attempts_used
        best_score = quiz_attempts.order_by("-score")[0].score

        return max_attempts, attempts_used, attempts_remaining, best_score

    def get_question_result(self, question, question_type, choices, user_answer):
        questionId = (question.id,)
        if question_type in ["single_choice", "multiple_choice"]:
            correctAnswer, userAnswer, isCorrect = self.get_selection_question_result(
                question, choices
            )
        elif question_type == "true_false":
            correctAnswer, userAnswer, isCorrect = self.get_true_false_question_result(
                question, user_answer
            )
        elif question_type == "short_answer":
            correctAnswer, userAnswer, isCorrect = (
                self.get_short_answer_question_result(question, user_answer)
            )
        explanation = (
            "Correct! Well done." if isCorrect else "Review the material and try again."
        )

        return {
            "questionId": questionId,
            "isCorrect": isCorrect,
            "correctAnswer": correctAnswer,
            "explanation": explanation,
            "userAnswer": userAnswer,
            "questionType": question_type,
        }, isCorrect

    def get_selection_question_result(self, question, choices):
        corrects = Choice.objects.filter(question=question, is_correct=True)
        correctAnswer = corrects.values_list("text", flat=True)
        userAnswer = choices.values_list("text", flat=True)
        isCorrect = corrects.values_list("id", flat=True) == choices.values_list(
            "id", flat=True
        )
        return correctAnswer, userAnswer, isCorrect

    def get_true_false_question_result(self, question, user_answer):
        correctAnswer = get_object_or_404(BooleanAnswer, question=question).answer
        userAnswer = user_answer
        isCorrect = correctAnswer == userAnswer
        return correctAnswer, userAnswer, isCorrect

    def get_short_answer_question_result(self, question, user_answer):
        correctAnswer = get_object_or_404(
            AcceptedAnswer, question=question
        ).answer.lower()
        userAnswer = user_answer.lower()
        isCorrect = correctAnswer == userAnswer
        return correctAnswer, userAnswer, isCorrect


class QuizSubmitApiView(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        enrollment = self.enrollment

        # Get quiz content with permission check
        quiz_content = get_object_or_404(
            QuizContent,
            content__lesson__id=lesson_id,
            content__lesson__section__course=enrollment.course,
            content__is_main_content=True,
        )

        # Get attempts in one query
        quiz_attempts = QuizAttempt.objects.filter(
            enrollment=enrollment, quiz=quiz_content
        ).order_by("-attempt_number")

        attempt_number = (
            quiz_attempts.first().attempt_number if quiz_attempts.exists() else 0
        )

        # Check max attempts (0 means unlimited)
        if (
            quiz_content.max_attempts > 0
            and attempt_number >= quiz_content.max_attempts
        ):
            return self.get_attempts_exceeded_response(quiz_content, quiz_attempts)

        # Validate answers
        answers_data = request.data.get("answers", [])
        if not answers_data:
            return Response({"error": "No answers provided"}, status=400)

        serializer = QuizSubmission(data=answers_data, many=True)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        # Process quiz submission atomically
        with transaction.atomic():
            quiz_attempt = QuizAttempt.objects.create(
                enrollment=enrollment,
                quiz=quiz_content,
                attempt_number=attempt_number + 1,
            )

            # Process all answers efficiently
            question_results, results = self.process_answers(
                serializer.validated_data, quiz_attempt
            )
            total_questions = len(results)
            correct_count = results.count(True)
            score_percentage = (
                (correct_count / total_questions * 100) if total_questions > 0 else 0
            )
            # Update attempt score
            quiz_attempt.score = score_percentage
            quiz_attempt.save(update_fields=["score"])

        # Prepare response
        return self.prepare_result(
            enrollment,
            lesson_id,
            quiz_content,
            question_results,
            results,
            quiz_attempts,
        )

    def process_answers(self, validated_data, quiz_attempt):
        """Process all answers with minimal queries"""
        question_ids = [answer["questionId"] for answer in validated_data]

        # Single query for all questions with related data
        # Use select_related for OneToOneField relations
        questions = (
            Question.objects.filter(id__in=question_ids)
            .select_related("boolean_answer")
            .prefetch_related(
                "choices",
                "accepted_answers",
            )
        )

        questions_dict = {q.id: q for q in questions}

        question_results = []
        results = []

        for answer_data in validated_data:
            question = questions_dict.get(answer_data["questionId"])
            if not question:
                continue

            question_type = answer_data["questionType"]

            # Process based on type
            if question_type in ["single_choice", "multiple_choice"]:
                result, is_correct = self.process_choice_question(
                    question, answer_data.get("selectedValues", []), quiz_attempt
                )
            elif question_type == "short_answer":
                result, is_correct = self.process_short_answer_question(
                    question, answer_data.get("textAnswer", ""), quiz_attempt
                )
            elif question_type == "true_false":
                result, is_correct = self.process_true_false_question(
                    question, answer_data.get("boolValue"), quiz_attempt
                )
            else:
                continue

            question_results.append(result)
            results.append(is_correct)

        return question_results, results

    def process_choice_question(self, question, selected_ids, quiz_attempt):
        """Process choice question"""
        # Single query for selected choices
        selected_choices = Choice.objects.filter(id__in=selected_ids, question=question)

        # Create quiz answer
        quiz_answer = QuizAnswer.objects.create(attempt=quiz_attempt, question=question)
        if selected_choices.exists():
            quiz_answer.selected_choices.set(selected_choices)

        # Get correct choices from prefetched data
        correct_choices = [
            choice for choice in question.choices.all() if choice.is_correct
        ]
        correct_ids = {choice.id for choice in correct_choices}
        selected_ids_set = set(selected_ids)

        is_correct = correct_ids == selected_ids_set

        return {
            "questionId": question.id,
            "isCorrect": is_correct,
            "correctAnswer": [choice.text for choice in correct_choices],
            "userAnswer": list(selected_choices.values_list("text", flat=True)),
            "questionType": "choice",
            "explanation": "Correct! Well done."
            if is_correct
            else "Review the material and try again.",
        }, is_correct

    def process_short_answer_question(self, question, user_answer, quiz_attempt):
        """Process short answer question"""
        QuizAnswer.objects.create(
            attempt=quiz_attempt, question=question, text_answer=user_answer
        )

        # Get accepted answer from select_related
        try:
            accepted_answers = question.accepted_answers.values_list(
                "answer", flat=True
            )
            print(accepted_answers)
            for accepted_answer in accepted_answers:
                is_correct = (
                    user_answer.lower().strip() == accepted_answer.lower().strip()
                )
                if is_correct:
                    break
        except AcceptedAnswer.DoesNotExist:
            accepted_answers = ["No accepted answer defined"]
            is_correct = False

        return {
            "questionId": question.id,
            "isCorrect": is_correct,
            "correctAnswer": ", ".join(accepted_answers),
            "userAnswer": user_answer,
            "questionType": "short_answer",
            "explanation": "Correct! Well done."
            if is_correct
            else "Review the material and try again.",
        }, is_correct

    def process_true_false_question(self, question, user_answer, quiz_attempt):
        """Process true/false question"""
        QuizAnswer.objects.create(
            attempt=quiz_attempt, question=question, bool_answer=user_answer
        )

        # Get boolean answer from select_related
        try:
            boolean_answer = question.boolean_answer  # OneToOneField
            correct_answer = boolean_answer.answer
            is_correct = correct_answer == user_answer
        except BooleanAnswer.DoesNotExist:
            correct_answer = None
            is_correct = False

        return {
            "questionId": question.id,
            "isCorrect": is_correct,
            "correctAnswer": correct_answer,
            "userAnswer": user_answer,
            "questionType": "true_false",
            "explanation": "Correct! Well done."
            if is_correct
            else "Review the material and try again.",
        }, is_correct

    def prepare_result(
        self,
        enrollment,
        lesson_id,
        quiz_content,
        question_results,
        results,
        quiz_attempts,
    ):
        """Prepare response with minimal queries"""
        total_questions = len(results)
        pass_score = quiz_content.passing_score
        score = results.count(True)
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        passed = percentage >= pass_score

        # Get attempts data
        max_attempts = quiz_content.max_attempts
        attempts_used = (
            quiz_attempts.first().attempt_number if quiz_attempts.exists() else 0
        )

        best_attempt = quiz_attempts.order_by("-score").first()
        best_score = best_attempt.score if best_attempt else 0

        # Handle lesson progress
        lesson = get_object_or_404(Lesson, id=lesson_id)
        lesson_progress, _ = LessonProgress.objects.get_or_create(
            lesson=lesson, enrollment=enrollment
        )

        lesson_completed = False
        if passed and lesson_progress.status != LessonProgress.Status.COMPLETED:
            lesson_progress.status = LessonProgress.Status.COMPLETED
            lesson_progress.completed_at = timezone.now()
            lesson_progress.save()
            lesson_completed = True
        elif lesson_progress.status == LessonProgress.Status.COMPLETED:
            lesson_completed = True

        # Get progress data in single optimized query
        progress_data = self.get_progress_data(enrollment)

        return Response(
            {
                "success": True,
                "score": score,
                "totalQuestions": total_questions,
                "percentage": round(percentage, 2),
                "passed": passed,
                "passScore": pass_score,
                "max_attempts": max_attempts,
                "attempts_used": attempts_used,
                "attempts_remaining": max(0, max_attempts - attempts_used)
                if max_attempts > 0
                else 999,
                "best_score": best_score,
                "questionResults": question_results
                if quiz_content.show_correct_answers
                else [],
                "includeCorrectAnswers": quiz_content.show_correct_answers,
                "lessonCompleted": lesson_completed,
                "completedLessons": progress_data["completed_lessons"],
                "completedCount": progress_data["completed_count"],
                "total_lessons": progress_data["total_lessons"],
                "overallProgress": progress_data["overall_progress"],
                "message": f"Passed with {round(percentage, 2)}%!"
                if passed
                else f"Scored {round(percentage, 2)}%. Need {pass_score}% to pass.",
            }
        )

    def get_progress_data(self, enrollment):
        """Get progress data in single optimized query"""
        from django.db.models import Count

        course = enrollment.course

        stats = Lesson.objects.filter(section__course=course).aggregate(
            total=Count("id"),
            completed=Count(
                "id",
                filter=Q(
                    progress_records__enrollment=enrollment,
                    progress_records__status=LessonProgress.Status.COMPLETED,
                ),
            ),
        )

        total = stats["total"] or 0
        completed = stats["completed"] or 0

        completed_lessons = list(
            Lesson.objects.filter(
                section__course=course,
                progress_records__enrollment=enrollment,
                progress_records__status=LessonProgress.Status.COMPLETED,
            ).values_list("id", flat=True)
        )

        return {
            "total_lessons": total,
            "completed_count": completed,
            "completed_lessons": completed_lessons,
            "overall_progress": int(completed / total * 100) if total > 0 else 0,
        }

    def get_attempts_exceeded_response(self, quiz_content, quiz_attempts):
        """Response when max attempts exceeded"""
        attempts_used = (
            quiz_attempts.first().attempt_number if quiz_attempts.exists() else 0
        )
        best_attempt = quiz_attempts.order_by("-score").first()
        best_score = best_attempt.score if best_attempt else 0

        return Response(
            {
                "success": False,
                "max_attempts": quiz_content.max_attempts,
                "attempts_used": attempts_used,
                "attempts_remaining": 0,
                "best_score": best_score,
                "message": f"Maximum attempts ({quiz_content.max_attempts}) reached",
            },
            status=400,
        )


class QuizSubmitAttemptsApiViewv1(EnrollmentResolverMixin, GenericAPIView):
    """
    success: true,
    lessonId: lessonId,
    attempts_used: attemptsUsed,
    max_attempts: maxAttempts,
    attempts_remaining: Math.max(0, maxAttempts - attemptsUsed),
    best_score: bestScore,
    last_score: lastScore,
    can_attempt: attemptsUsed < maxAttempts

    """

    permission_classes = [IsEnrolled]

    def get(self, request, enrollment_id, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        quiz = QuizContent.objects.filter(content__lesson=lesson)[0]
        quiz_attempts = QuizAttempt.objects.filter(
            quiz=quiz, enrollment=self.enrollment
        )
        attempts_used = 0
        best_score = None
        last_score = None
        if quiz_attempts.exists():
            attempts_used = quiz_attempts.order_by("-attempt_number")[0].attempt_number
            best_score = quiz_attempts.order_by("-score")[0].score
            last_score = quiz_attempts.order_by("-attempt_number")[0].score
        max_attempts = quiz.max_attempts
        data = {
            "success": True,
            "lessonId": lesson.id,
            "attempts_used": attempts_used,
            "max_attempts": quiz.max_attempts,
            "attempts_remaining": max_attempts - attempts_used,
            "best_score": best_score,
            "last_score": last_score,
            "can_attempt": attempts_used < max_attempts,
        }

        return Response(data)


class QuizSubmitAttemptsApiView(EnrollmentResolverMixin, GenericAPIView):
    """
    Get quiz attempt statistics for a lesson.
    Returns:
        - success: bool
        - lessonId: int
        - attempts_used: int
        - max_attempts: int (0 means unlimited)
        - attempts_remaining: int
        - best_score: int or None
        - last_score: int or None
        - can_attempt: bool
    """

    permission_classes = [IsEnrolled]

    def get(self, request, enrollment_id, lesson_id):
        enrollment = self.enrollment

        # Verify lesson belongs to course
        lesson = get_object_or_404(
            Lesson, id=lesson_id, section__course=enrollment.course
        )

        # Get quiz content
        quiz = get_object_or_404(QuizContent, content__lesson=lesson)

        # Get attempts data in ONE optimized query
        attempts_data = self.get_attempts_data(quiz, enrollment)

        return Response(
            {
                "success": True,
                "lessonId": lesson.id,
                "attempts_used": attempts_data["attempts_used"],
                "max_attempts": attempts_data["max_attempts"],
                "attempts_remaining": attempts_data["attempts_remaining"],
                "best_score": attempts_data["best_score"],
                "last_score": attempts_data["last_score"],
                "can_attempt": attempts_data["can_attempt"],
            }
        )

    def get_attempts_data(self, quiz, enrollment):
        """Get all attempt statistics in one query using aggregation"""
        from django.db.models import Count, Max

        # Single aggregation query
        attempts = QuizAttempt.objects.filter(
            quiz=quiz, enrollment=enrollment
        ).aggregate(
            total_attempts=Count("id"),
            max_attempt_number=Max("attempt_number"),
            best_score=Max("score"),
        )

        # Get last attempt in a separate query (or use ordering)
        last_attempt = (
            QuizAttempt.objects.filter(quiz=quiz, enrollment=enrollment)
            .order_by("-attempt_number")
            .first()
        )

        attempts_used = attempts["max_attempt_number"] or 0
        best_score = attempts["best_score"]
        last_score = last_attempt.score if last_attempt else None

        max_attempts = quiz.max_attempts

        # Handle unlimited attempts (max_attempts = 0)
        if max_attempts == 0:
            attempts_remaining = float("inf")  # Or use None / "Unlimited"
            can_attempt = True
        else:
            attempts_remaining = max(0, max_attempts - attempts_used)
            can_attempt = attempts_used < max_attempts

        return {
            "attempts_used": attempts_used,
            "max_attempts": max_attempts,
            "attempts_remaining": attempts_remaining,
            "best_score": best_score,
            "last_score": last_score,
            "can_attempt": can_attempt,
        }


class AssignmentApiView1(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def get(self, request, enrollment_id, lesson_id):
        """
        success: true,
        lessonId: lessonId,
        assignment: assignmentData,
            instructions: 'Build a data analysis project using Python. Analyze a dataset of your choice and present your findings with visualizations.',
            maxScore: 100,
            dueDate: '2024-12-31T23:59:59Z',
            allowLateSubmission: false,
            maxAttempts: 3,
            acceptedFileTypes: 'pdf,docx,zip,py',
            maxFileSizeMB: 50
        submissions: submissions,
        attempts_used: submissions.length,
        max_attempts: assignmentData?.maxAttempts || 1,
        attempts_remaining: Math.max(0, (assignmentData?.maxAttempts || 1) - submissions.length),
        can_submit: submissions.length < (assignmentData?.maxAttempts || 1)
        """

        lesson = get_object_or_404(
            Lesson, id=lesson_id, section__course__enrollments=self.enrollment
        )
        content = get_object_or_404(LessonContent, lesson=lesson, is_main_content=True)
        max_attempts, assignmentData = self.get_assignment_data(content.assignment)
        attempts_used, submissions = self.get_assignment_submissions(
            content.assignment, self.enrollment
        )
        attempts_remaining = max_attempts - attempts_used
        data = {
            "success": True,
            "lessonId": lesson.id,
            "assignment": assignmentData,
            "submissions": submissions,
            "attempts_used": attempts_used,
            "max_attempts": max_attempts,
            "attempts_remaining": attempts_remaining,
            "can_submit": attempts_used < max_attempts,
        }
        return Response(data)

    def get_assignment_data(self, assignment):
        serializer = AssignmentSerializer(instance=assignment)
        max_attempts = assignment.max_attempts
        return max_attempts, serializer.data

    def get_assignment_submissions(self, assignment, enrollment):
        """
        attemptNumber: submissions.length + 1,
        status: 'submitted',
        submissionText: submissionData.submissionText || '',
        files: submissionData.files || [],
        score: null,
        feedback: '',
        submittedAt: new Date().toISOString(),
        gradedAt: null
        """

        submissions = assignment.submissions.filter(enrollment=enrollment)

        attempts_used = submissions.count()

        serializer = AssignmentSubmissionSerializer(instance=submissions, many=True)
        return attempts_used, serializer.data


class AssignmentApiView(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def get(self, request, enrollment_id, lesson_id):
        enrollment = self.enrollment

        # Verify lesson belongs to course
        lesson = get_object_or_404(
            Lesson, id=lesson_id, section__course=enrollment.course
        )

        # Use filter().select_related() first, then get()
        content = get_object_or_404(
            LessonContent.objects.select_related("assignment"),
            lesson=lesson,
            is_main_content=True,
            content_type=LessonContent.Type.ASSIGNMENT,
        )

        assignment = content.assignment

        # Get submissions with related data
        submissions = (
            AssignmentSubmission.objects.filter(
                assignment=assignment, enrollment=enrollment
            )
            .select_related("enrollment", "enrollment__user")
            .order_by("-submitted_at")
        )

        attempts_used = submissions.count()

        # Serialize
        assignment_data = AssignmentSerializer(assignment).data
        submissions_data = AssignmentSubmissionSerializer(submissions, many=True).data

        # Handle unlimited attempts
        max_attempts = assignment.max_attempts
        if max_attempts == 0:
            attempts_remaining = "Unlimited"
            can_submit = True
        else:
            attempts_remaining = max(0, max_attempts - attempts_used)
            can_submit = attempts_used < max_attempts

        return Response(
            {
                "success": True,
                "lessonId": lesson.id,
                "assignment": assignment_data,
                "submissions": submissions_data,
                "attempts_used": attempts_used,
                "max_attempts": max_attempts,
                "attempts_remaining": attempts_remaining,
                "can_submit": can_submit,
            }
        )


class AssignmentSubmissionApiViewv1(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        lesson = get_object_or_404(
            Lesson, id=lesson_id, section__course__enrollments=self.enrollment
        )
        assignment = get_object_or_404(
            LessonContent, lesson=lesson, is_main_content=True
        ).assignment
        submissions = assignment.submissions.filter(enrollment=self.enrollment)
        submission_text = request.data.get("submission_text")

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=self.enrollment,
            attempt_number=submissions.count() + 1,
            status=AssignmentSubmission.Status.SUBMITTED,
            submission_text=submission_text,
            submitted_at=timezone.now(),
        )

        files = request.FILES.getlist("files") if request else []
        for file in files:
            AssignmentSubmissionFile.objects.create(submission=submission, file=file)
        file_serialier = AssignmentSubmissionFileSerializer(
            instance=submission.files, many=True
        )
        new_submission = {
            "attemptNumber": submission.attempt_number,
            "status": AssignmentSubmission.Status.SUBMITTED,
            "submissionText": submission.submission_text,
            "files": file_serialier.data,
            "score": None,
            "feedback": "",
            "submittedAt": submission.submitted_at,
            "gradedAt": None,
        }
        submissions = assignment.submissions.filter(enrollment=self.enrollment)
        data = {
            "success": True,
            "submission": new_submission,
            "attempts_used": submissions.count(),
            "message": "Assignment submitted successfully!",
        }
        return Response(data)


class AssignmentSubmissionApiView(EnrollmentResolverMixin, GenericAPIView):
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id, lesson_id):
        enrollment = self.enrollment

        # Get lesson with select_related
        lesson = get_object_or_404(
            Lesson.objects.select_related("section__course"),
            id=lesson_id,
            section__course=enrollment.course,
        )

        # Get assignment content with select_related
        content = get_object_or_404(
            LessonContent.objects.select_related("assignment"),
            lesson=lesson,
            is_main_content=True,
            content_type=LessonContent.Type.ASSIGNMENT,
        )

        assignment = content.assignment

        # Check if user can submit
        submissions_count = assignment.submissions.filter(enrollment=enrollment).count()
        max_attempts = assignment.max_attempts

        if max_attempts > 0 and submissions_count >= max_attempts:
            return Response(
                {
                    "success": False,
                    "error": "Maximum attempts reached",
                    "max_attempts": max_attempts,
                    "attempts_used": submissions_count,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate submission text (if required)
        submission_text = request.data.get("submission_text", "")

        # Validate files
        files = request.FILES.getlist("files", [])
        if not self.validate_files(files, assignment):
            return Response(
                {
                    "success": False,
                    "error": "Invalid file(s). Check file types and sizes.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create submission atomically
        with transaction.atomic():
            # Create the submission
            submission = AssignmentSubmission.objects.create(
                assignment=assignment,
                enrollment=enrollment,
                attempt_number=submissions_count + 1,
                status=AssignmentSubmission.Status.SUBMITTED,
                submission_text=submission_text,
                submitted_at=timezone.now(),
            )

            # Create file records
            for file in files:
                AssignmentSubmissionFile.objects.create(
                    submission=submission, file=file
                )

        # Serialize the new submission
        file_serializer = AssignmentSubmissionFileSerializer(
            instance=submission.files.all(), many=True
        )

        new_submission = {
            "attemptNumber": submission.attempt_number,
            "status": submission.status,
            "submissionText": submission.submission_text,
            "files": file_serializer.data,
            "score": submission.score,
            "feedback": submission.feedback,
            "submittedAt": submission.submitted_at,
            "gradedAt": submission.graded_at,
        }

        # Calculate remaining attempts
        new_submissions_count = submissions_count + 1
        if max_attempts == 0:
            attempts_remaining = "Unlimited"
            can_submit = True
        else:
            attempts_remaining = max(0, max_attempts - new_submissions_count)
            can_submit = new_submissions_count < max_attempts

        return Response(
            {
                "success": True,
                "submission": new_submission,
                "attempts_used": new_submissions_count,
                "max_attempts": max_attempts,
                "attempts_remaining": attempts_remaining,
                "can_submit": can_submit,
                "message": "Assignment submitted successfully!",
            }
        )

    def validate_files(self, files, assignment):
        """Validate uploaded files against assignment requirements"""
        if not files:
            return True  # Files might be optional

        # Check file count (if there's a limit)
        # max_files = getattr(assignment, 'max_files', None)
        # if max_files and len(files) > max_files:
        #     return False

        accepted_types = (
            getattr(assignment, "accepted_file_types", "").lower().split(",")
        )
        max_size_mb = getattr(assignment, "max_file_size_mb", 50)
        max_size_bytes = max_size_mb * 1024 * 1024

        for file in files:
            # Check file size
            if file.size > max_size_bytes:
                return False

            # Check file type
            if accepted_types:
                file_extension = file.name.split(".")[-1].lower()
                if file_extension not in accepted_types:
                    return False

        return True


class CourseEnrollment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        enrollment, _created = Enrollment.objects.get_or_create(
            course=course, user=request.user
        )
        return Response({"enrollment_id": enrollment.id})


# **********
class StudentCoursesApiView(ListAPIView):
    serializer_class = StudentCourseSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        user = self.request.user
        enrollment = Enrollment.objects.filter(course=OuterRef("pk"), user=user)
        return (
            Course.objects.filter(
                enrollments__user=user,
                enrollments__status__in=[
                    Enrollment.Status.ACTIVE,
                    Enrollment.Status.COMPLETED,
                ],
            )
            .annotate(
                rating=Avg("enrollments__feedback__rating"),
                enrollment_id=Subquery(enrollment.values("id")[:1]),
                progress=Subquery(enrollment.values("progress")[:1]),
                enrollment_status=Subquery(enrollment.values("status")[:1]),
                last_accessed=Subquery(enrollment.values("last_activity_at")[:1]),
                enrolled_at=Subquery(enrollment.values("enrolled_at")[:1]),
            )
            .select_related("category", "owner")
            .distinct()
            .order_by("-enrolled_at")
        )


class StudentWishlistApiView(ListAPIView):
    serializer_class = StudentWishlistSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        user = self.request.user
        return (
            CourseWishlist.objects.filter(user=user)
            .select_related(
                "course",
                "course__category",
                "course__owner",
            )
            .annotate(
                rating=Avg("course__enrollments__feedback__rating"),
                rating_count=Count("course__enrollments__feedback", distinct=True),
            )
            .order_by("-created_at")
        )


class StudentCertificatesApiView(ListAPIView):
    permission_classes = [IsStudent]
    serializer_class = StudentCourseCertificateSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Certificate.objects.filter(enrollment__user=user)
            .select_related(
                "enrollment",
                "enrollment__course",
                "enrollment__user",
            )
            .order_by("-issued_at")
        )


class CertificateDownloadApiView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        certificate = get_object_or_404(
            Certificate, pk=pk, enrollment__user=request.user
        )

        return FileResponse(
            certificate.file.open("rb"),
            as_attachment=True,
            filename=f"{certificate.certificate_number}.pdf",
            content_type="application/pdf",
        )
