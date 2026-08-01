"""
Field name constants. Centralizing these makes refactoring easier
and prevents typos from hardcoded strings scattered everywhere.
"""

# Course-level fields
FIELD_TITLE = "title"
FIELD_SUBTITLE = "subtitle"
FIELD_SHORT_DESCRIPTION = "short_description"
FIELD_CATEGORY = "category"
FIELD_SUBCATEGORY = "subcategory"
FIELD_LEVEL = "level"
FIELD_LANGUAGE = "language"
FIELD_DURATION = "duration"
FIELD_VISIBILITY = "visibility"
FIELD_DESCRIPTION = "description"
FIELD_PRICE_TYPE = "price_type"
FIELD_PRICE = "price"
FIELD_PRICE_DISCOUNT = "price_discount"
FIELD_SEO_TITLE = "seoTitle"
FIELD_SEO_DESCRIPTION = "seoDescription"
FIELD_VERSION = "version"
FIELD_VERSION_NOTE = "version_note"
FIELD_STATUS = "status"
FIELD_REVIEW_STATUS = "reviewStatus"

# File upload fields
FIELD_THUMBNAIL = "thumbnail"
FIELD_PROMO_VIDEO = "promo_video"
FIELD_COURSE_TRAILER = "course_trailer"

# Array fields (flat indexed in form data)
FIELD_OUTCOMES = "outcomes"
FIELD_PREREQUISITES = "prerequisites"
FIELD_TARGET_AUDIENCE = "targetAudience"
FIELD_TAGS = "tags"

# Attachment fields
FIELD_ATTACHMENT_FILES = "attachment_files"

# Section/Lesson structural prefixes
PREFIX_SECTIONS = "sections"
PREFIX_LESSONS = "lessons"
PREFIX_CONTENT = "content"

# Section fields
FIELD_SECTION_ID = "id"
FIELD_SECTION_TITLE = "title"
FIELD_SECTION_DESCRIPTION = "description"
FIELD_SECTION_DURATION = "duration"

# Lesson fields
FIELD_LESSON_ID = "id"
FIELD_LESSON_TITLE = "title"
FIELD_LESSON_DESCRIPTION = "description"
FIELD_LESSON_DURATION = "duration"
FIELD_LESSON_PUBLISHED = "published"
FIELD_LESSON_PREVIEW = "preview"
FIELD_LESSON_TYPE = "type"
FIELD_LESSON_COMPLETION_RULE = "completionRule"

# Content types
CONTENT_TYPE_VIDEO = "video"
CONTENT_TYPE_ARTICLE = "article"
CONTENT_TYPE_QUIZ = "quiz"
CONTENT_TYPE_ASSIGNMENT = "assignment"
CONTENT_TYPE_FILE = "file"

# Content field suffixes (relative to content base)
CONTENT_TEXT = "text"
CONTENT_TEXT_CONTENT = "textContent"
CONTENT_TRANSCRIPT = "transcript"
CONTENT_VIDEO_URL = "videoUrl"
CONTENT_VIDEO_FILE = "videoFile"
CONTENT_FILE_URL = "fileUrl"
CONTENT_FILE = "file"

# Quiz specific
CONTENT_QUIZ_SETTINGS = "quizSettings"
QUIZ_INSTRUCTIONS = "instructions"
QUIZ_PASSING_SCORE = "passingScore"
QUIZ_TIME_LIMIT = "timeLimit"
QUIZ_MAX_ATTEMPTS = "maxAttempts"
QUIZ_SHUFFLE_QUESTIONS = "shuffleQuestions"
QUIZ_SHUFFLE_CHOICES = "shuffleChoices"
QUIZ_SHOW_CORRECT = "showCorrectAnswers"
QUIZ_QUESTIONS = "questions"

# Question fields
QUESTION_TYPE = "question_type"
QUESTION_TEXT = "text"
QUESTION_DIFFICULTY = "difficulty"
QUESTION_POINTS = "points"
QUESTION_EXPLANATION = "explanation"
QUESTION_REQUIRED = "is_required"
QUESTION_TIME = "estimated_time"
QUESTION_ORDER = "order"
QUESTION_CORRECT = "correct"
QUESTION_OPTIONS = "options"
QUESTION_ACCEPTED_ANSWERS = "accepted_answers"

# Assignment specific
ASSIGNMENT_INSTRUCTIONS = "instructions"
ASSIGNMENT_MAX_SCORE = "maxScore"
ASSIGNMENT_ALLOW_LATE = "allowLateSubmission"
ASSIGNMENT_MAX_ATTEMPTS = "maxAttempts"
ASSIGNMENT_FILE_TYPES = "acceptedFileTypes"
ASSIGNMENT_FILE_SIZE = "maxFileSizeMb"
ASSIGNMENT_DUE_DATE = "dueDate"

# Video caption fields
CAPTIONS_PREFIX = "captions"
CAPTION_LANGUAGE = "language"
CAPTION_LABEL = "label"
CAPTION_FILE_NAME = "fileName"
CAPTION_FILE_SIZE = "fileSize"
CAPTION_IS_DEFAULT = "is_default"
CAPTION_FILE = "file"
CAPTION_FORMAT = "file_format"
