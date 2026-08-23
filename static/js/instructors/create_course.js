// ============================================
// CREATE COURSE PAGE CONTROLLER
// ============================================
const baseUrl = window.location.origin;

function buildFormData(data, formData = new FormData(), parentKey = '') {

    if (data === null || data === undefined) {
        return formData;
    }

    // Handle Files and Blobs
    if (data instanceof File || data instanceof Blob) {
        formData.append(parentKey, data);
        return formData;
    }

    // Handle Arrays
    if (Array.isArray(data)) {
        data.forEach((item, index) => {
            const key = parentKey ? `${parentKey}[${index}]` : `${index}`;
            if (typeof item === 'object' && item !== null && !(item instanceof File)) {
                buildFormData(item, formData, key);
            } else if (item !== null && item !== undefined && item !== '') {
                formData.append(key, item);
            }
        });
        return formData;
    }

    // Handle Objects
    if (typeof data === 'object') {
        Object.keys(data).forEach(key => {
            const value = data[key];
            const newKey = parentKey ? `${parentKey}.${key}` : key;

            // Skip id fields for new course creation
            if (key === 'id' || key === 'deleted') {
                return;
            }

            // Skip thumbnailPreview (not needed for FormData)
            if (key === 'thumbnailPreview') {
                return;
            }

            // Skip attachments metadata array (we use attachment_files)
            if (key === 'attachments') {
                return;
            }

            // Skip versionHistory
            if (key === 'versionHistory') {
                return;
            }

            // Skip lastUpdated, status, reviewStatus for create
            if (key === 'lastUpdated' || key === 'status' || key === 'reviewStatus') {
                return;
            }

            // Handle special cases for file fields
            if (key === 'thumbnail' || key === 'promoVideo' || key === 'courseTrailer') {
                if (value instanceof File) {
                    formData.append(newKey, value);
                } else if (typeof value === 'string' && value !== '') {
                    formData.append(newKey, value);
                }
                return;
            }

            // Handle attachment_files array
            if (key === 'attachment_files') {
                if (Array.isArray(value)) {
                    value.forEach((file, index) => {
                        if (file instanceof File) {
                            formData.append(`${newKey}[${index}]`, file);
                        }
                    });
                }
                return;
            }

            // Handle sections array
            if (key === 'sections' && Array.isArray(value)) {
                value.forEach((section, sectionIndex) => {
                    const sectionKey = `${newKey}[${sectionIndex}]`;

                    // Send section order
                    formData.append(`${sectionKey}.order`, sectionIndex);

                    // Send section title
                    if (section.title !== undefined && section.title !== '') {
                        formData.append(`${sectionKey}.title`, section.title);
                    }

                    // Send section description
                    if (section.description !== undefined && section.description !== '') {
                        formData.append(`${sectionKey}.description`, section.description);
                    }

                    // Send section duration
                    if (section.duration !== undefined && section.duration !== '') {
                        formData.append(`${sectionKey}.duration`, section.duration);
                    }

                    // Process lessons within each section
                    if (section.lessons && Array.isArray(section.lessons)) {
                        section.lessons.forEach((lesson, lessonIndex) => {
                            const lessonKey = `${sectionKey}.lessons[${lessonIndex}]`;

                            // Send lesson order
                            formData.append(`${lessonKey}.order`, lessonIndex);

                            // Send lesson title
                            if (lesson.title !== undefined && lesson.title !== '') {
                                formData.append(`${lessonKey}.title`, lesson.title);
                            }

                            // Send lesson description
                            if (lesson.description !== undefined && lesson.description !== '') {
                                formData.append(`${lessonKey}.description`, lesson.description);
                            }

                            // Send lesson duration
                            if (lesson.duration !== undefined && lesson.duration !== '') {
                                formData.append(`${lessonKey}.duration`, lesson.duration);
                            }

                            // Send preview and published
                            formData.append(`${lessonKey}.preview`, lesson.preview ? 'true' : 'false');
                            formData.append(`${lessonKey}.published`, lesson.published ? 'true' : 'false');

                            // Send completion_criteria
                            if (lesson.completion_criteria && typeof lesson.completion_criteria === 'object') {
                                const criteriaKey = `${lessonKey}.completion_criteria`;

                                if (lesson.completion_criteria.criteria_type) {
                                    formData.append(`${criteriaKey}.criteria_type`, lesson.completion_criteria.criteria_type);
                                }

                                if (lesson.completion_criteria.video_watch_percentage !== undefined && lesson.completion_criteria.video_watch_percentage !== null) {
                                    formData.append(`${criteriaKey}.video_watch_percentage`, lesson.completion_criteria.video_watch_percentage);
                                }

                                if (lesson.completion_criteria.quiz_passing_score !== undefined && lesson.completion_criteria.quiz_passing_score !== null) {
                                    formData.append(`${criteriaKey}.quiz_passing_score`, lesson.completion_criteria.quiz_passing_score);
                                }

                                // Always send deleted as false for new
                                formData.append(`${criteriaKey}.deleted`, 'false');
                            }

                            // Process content within each lesson
                            if (lesson.content && typeof lesson.content === 'object') {
                                const contentKey = `${lessonKey}.content`;

                                // Send content_type based on lesson type
                                formData.append(`${contentKey}.content_type`, lesson.type);

                                // Handle video content
                                if (lesson.type === 'video') {
                                    const videoKey = `${contentKey}.video`;

                                    // Determine video source
                                    const videoSource = lesson.content.videoSource || 'file';
                                    formData.append(`${videoKey}.video_source`, videoSource);

                                    // Send video file if exists
                                    if (lesson.content.videoFile instanceof File) {
                                        formData.append(`${videoKey}.video_file`, lesson.content.videoFile);
                                    }

                                    // Send external URL if source is url
                                    if (videoSource === 'url' && lesson.content.videoUrl) {
                                        formData.append(`${videoKey}.external_url`, lesson.content.videoUrl);
                                    }

                                    // Send text content
                                    if (lesson.content.textContent) {
                                        formData.append(`${videoKey}.text`, lesson.content.textContent);
                                    }

                                    // Send transcript
                                    if (lesson.content.transcript) {
                                        formData.append(`${videoKey}.transcript`, lesson.content.transcript);
                                    }

                                    // Send duration
                                    if (lesson.content.duration || lesson.duration) {
                                        formData.append(`${videoKey}.duration`, lesson.content.duration || lesson.duration);
                                    }

                                    // Always send deleted as false
                                    formData.append(`${videoKey}.deleted`, 'false');

                                    // Handle captions
                                    if (lesson.content.captions && Array.isArray(lesson.content.captions)) {
                                        lesson.content.captions.forEach((caption, captionIndex) => {
                                            const captionKey = `${contentKey}.captions[${captionIndex}]`;

                                            if (caption.file instanceof File) {
                                                formData.append(`${captionKey}.file`, caption.file);
                                            }

                                            if (caption.language) {
                                                formData.append(`${captionKey}.language`, caption.language);
                                            }

                                            if (caption.label) {
                                                formData.append(`${captionKey}.label`, caption.label);
                                            }

                                            if (caption.fileFormat) {
                                                formData.append(`${captionKey}.file_format`, caption.fileFormat);
                                            }

                                            formData.append(`${captionKey}.is_default`, caption.isDefault ? 'true' : 'false');
                                        });
                                    }

                                    // Handle attachment files
                                    if (lesson.content.attachment_files && Array.isArray(lesson.content.attachment_files)) {
                                        lesson.content.attachment_files.forEach((file, fileIndex) => {
                                            if (file instanceof File) {
                                                formData.append(`${contentKey}.attachments[${fileIndex}].file`, file);
                                            }
                                        });
                                    }
                                }
                                // Handle article content
                                else if (lesson.type === 'article') {
                                    const articleKey = `${contentKey}.article`;

                                    if (lesson.content.text) {
                                        formData.append(`${articleKey}.body`, lesson.content.text);
                                    }

                                    formData.append(`${articleKey}.deleted`, 'false');

                                    // Handle attachment files
                                    if (lesson.content.attachment_files && Array.isArray(lesson.content.attachment_files)) {
                                        lesson.content.attachment_files.forEach((file, fileIndex) => {
                                            if (file instanceof File) {
                                                formData.append(`${contentKey}.attachments[${fileIndex}].file`, file);
                                            }
                                        });
                                    }
                                }
                                // Handle file content
                                else if (lesson.type === 'file') {
                                    const fileContentKey = `${contentKey}.file_content`;

                                    if (lesson.content.file instanceof File) {
                                        formData.append(`${fileContentKey}.file`, lesson.content.file);
                                    }

                                    if (lesson.content.fileUrl) {
                                        formData.append(`${fileContentKey}.file_url`, lesson.content.fileUrl);
                                    }

                                    formData.append(`${fileContentKey}.deleted`, 'false');

                                    // Handle attachment files
                                    if (lesson.content.attachment_files && Array.isArray(lesson.content.attachment_files)) {
                                        lesson.content.attachment_files.forEach((file, fileIndex) => {
                                            if (file instanceof File) {
                                                formData.append(`${contentKey}.attachments[${fileIndex}].file`, file);
                                            }
                                        });
                                    }
                                }
                                // Handle quiz content
                                else if (lesson.type === 'quiz') {
                                    // Send quiz settings
                                    if (lesson.content.quizSettings) {
                                        const quizSettings = lesson.content.quizSettings;

                                        if (quizSettings.instructions) {
                                            formData.append(`${contentKey}.quizSettings.instructions`, quizSettings.instructions);
                                        }
                                        formData.append(`${contentKey}.quizSettings.passingScore`, quizSettings.passingScore || 70);

                                        if (quizSettings.timeLimit !== null && quizSettings.timeLimit !== undefined) {
                                            formData.append(`${contentKey}.quizSettings.timeLimit`, quizSettings.timeLimit);
                                        }
                                        formData.append(`${contentKey}.quizSettings.maxAttempts`, quizSettings.maxAttempts || 1);
                                        formData.append(`${contentKey}.quizSettings.shuffleQuestions`, quizSettings.shuffleQuestions ? 'true' : 'false');
                                        formData.append(`${contentKey}.quizSettings.shuffleChoices`, quizSettings.shuffleChoices ? 'true' : 'false');
                                        formData.append(`${contentKey}.quizSettings.showCorrectAnswers`, quizSettings.showCorrectAnswers ? 'true' : 'false');
                                    }

                                    // Send questions
                                    if (lesson.content.questions && Array.isArray(lesson.content.questions)) {
                                        lesson.content.questions.forEach((question, questionIndex) => {
                                            const questionKey = `${contentKey}.questions[${questionIndex}]`;

                                            if (question.text) {
                                                formData.append(`${questionKey}.text`, question.text);
                                            }

                                            formData.append(`${questionKey}.question_type`, question.question_type || 'single_choice');
                                            formData.append(`${questionKey}.difficulty`, question.difficulty || 'medium');
                                            formData.append(`${questionKey}.points`, question.points || 1);
                                            formData.append(`${questionKey}.is_required`, question.is_required ? 'true' : 'false');
                                            formData.append(`${questionKey}.order`, questionIndex + 1);

                                            if (question.estimated_time !== null && question.estimated_time !== undefined) {
                                                formData.append(`${questionKey}.estimated_time`, question.estimated_time);
                                            }

                                            if (question.explanation) {
                                                formData.append(`${questionKey}.explanation`, question.explanation);
                                            }

                                            // Handle options/choices for single and multiple choice
                                            if ((question.question_type === 'single_choice' || question.question_type === 'multiple_choice') && question.options && Array.isArray(question.options)) {
                                                question.options.forEach((option, optionIndex) => {
                                                    if (option !== '' && option !== undefined && option !== null) {
                                                        const isCorrect = question.question_type === 'single_choice'
                                                            ? question.correct === optionIndex
                                                            : (Array.isArray(question.correct) && question.correct.includes(optionIndex));

                                                        formData.append(`${questionKey}.choices[${optionIndex}].text`, option);
                                                        formData.append(`${questionKey}.choices[${optionIndex}].is_correct`, isCorrect ? 'true' : 'false');
                                                        formData.append(`${questionKey}.choices[${optionIndex}].order`, optionIndex);
                                                    }
                                                });
                                            }

                                            // Handle true/false
                                            if (question.question_type === 'true_false') {
                                                formData.append(`${questionKey}.correct`, question.correct === true || question.correct === 'true' ? 'true' : 'false');
                                            }

                                            // Handle accepted answers for short_answer
                                            if (question.question_type === 'short_answer' && question.accepted_answers && Array.isArray(question.accepted_answers)) {
                                                question.accepted_answers.forEach((answer, answerIndex) => {
                                                    if (answer !== '' && answer !== undefined && answer !== null) {
                                                        formData.append(`${questionKey}.accepted_answers[${answerIndex}].answer`, answer);
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    // Handle attachment files
                                    if (lesson.content.attachment_files && Array.isArray(lesson.content.attachment_files)) {
                                        lesson.content.attachment_files.forEach((file, fileIndex) => {
                                            if (file instanceof File) {
                                                formData.append(`${contentKey}.attachments[${fileIndex}].file`, file);
                                            }
                                        });
                                    }
                                }
                                // Handle assignment content
                                else if (lesson.type === 'assignment') {
                                    const assignmentKey = `${contentKey}.assignment`;

                                    if (lesson.content.instructions) {
                                        formData.append(`${assignmentKey}.instructions`, lesson.content.instructions);
                                    }

                                    formData.append(`${assignmentKey}.max_score`, lesson.content.maxScore || 100);

                                    if (lesson.content.dueDate) {
                                        formData.append(`${assignmentKey}.due_date`, lesson.content.dueDate);
                                    }

                                    formData.append(`${assignmentKey}.allow_late_submission`, lesson.content.allowLateSubmission ? 'true' : 'false');
                                    formData.append(`${assignmentKey}.max_attempts`, lesson.content.maxAttempts || 1);

                                    if (lesson.content.acceptedFileTypes) {
                                        formData.append(`${assignmentKey}.accepted_file_types`, lesson.content.acceptedFileTypes);
                                    }

                                    formData.append(`${assignmentKey}.max_file_size_mb`, lesson.content.maxFileSizeMb || 50);
                                    formData.append(`${assignmentKey}.deleted`, 'false');

                                    // Handle attachment files
                                    if (lesson.content.attachment_files && Array.isArray(lesson.content.attachment_files)) {
                                        lesson.content.attachment_files.forEach((file, fileIndex) => {
                                            if (file instanceof File) {
                                                formData.append(`${contentKey}.attachments[${fileIndex}].file`, file);
                                            }
                                        });
                                    }
                                }
                            }
                        });
                    }
                });
                return;
            }

            // Handle features array - send as features[index].text and features[index].icon
            if (key === 'features' && Array.isArray(value)) {
                value.forEach((feature, featureIndex) => {
                    if (feature.deleted) return;

                    const featureKey = `${newKey}[${featureIndex}]`;

                    if (feature.text) {
                        formData.append(`${featureKey}.text`, feature.text);
                    }

                    if (feature.icon) {
                        formData.append(`${featureKey}.icon`, feature.icon);
                    }
                });
                return;
            }

            // Handle outcomes array - send as learning_outcomes[index].description
            if (key === 'outcomes' && Array.isArray(value)) {
                value.forEach((outcome, outcomeIndex) => {
                    if (outcome !== '' && outcome !== undefined && outcome !== null) {
                        formData.append(`learning_outcomes[${outcomeIndex}].description`, outcome);
                    }
                });
                return;
            }

            // Handle prerequisites array - send as prerequisites[index].description
            if (key === 'prerequisites' && Array.isArray(value)) {
                value.forEach((prerequisite, prereqIndex) => {
                    if (prerequisite !== '' && prerequisite !== undefined && prerequisite !== null) {
                        formData.append(`prerequisites[${prereqIndex}].description`, prerequisite);
                    }
                });
                return;
            }

            // Handle targetAudience array - send as target_audiences[index].description
            if (key === 'targetAudience' && Array.isArray(value)) {
                value.forEach((audience, audienceIndex) => {
                    if (audience !== '' && audience !== undefined && audience !== null) {
                        formData.append(`target_audiences[${audienceIndex}].description`, audience);
                    }
                });
                return;
            }

            // Handle tags array - send as tags[index].name
            if (key === 'tags' && Array.isArray(value)) {
                value.forEach((tag, tagIndex) => {
                    if (tag !== '' && tag !== undefined && tag !== null) {
                        formData.append(`tags[${tagIndex}].name`, tag);
                    }
                });
                return;
            }

            if (value instanceof Date) {
                formData.append(newKey, value.toISOString());
                return;
            }

            if (typeof value === 'object' && value !== null && !(value instanceof File)) {
                buildFormData(value, formData, newKey);
            } else if (value !== null && value !== undefined && value !== '') {
                formData.append(newKey, value);
            }
        });
        return formData;
    }

    if (parentKey && data !== '' && data !== null && data !== undefined) {
        formData.append(parentKey, data);
    }
    return formData;
}

function mapData(courseData) {
    const { shortDescription, promoVideo, courseTrailer, priceType, discountPrice, fullDescription, thumbnailPreview, versionNotes, ...rest } = courseData;
    const payload = {
        ...rest,
        short_description: shortDescription,
        promo_video: promoVideo,
        course_trailer: courseTrailer,
        price_type: priceType,
        price_discount: discountPrice,
        description: fullDescription,
        version_note: versionNotes
    };

    return payload;
}

class CreateCoursePage {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 8;
        this.courseData = this.getDefaultData();
        this.autoSaveTimer = null;
        this.editingLesson = null;
        this.courseLanguages = [];
        this.courseLevels = [];
        this.courseCategories = [];
        this.dragState = {
            active: false,
            type: null,
            sourceSection: null,
            sourceLesson: null,
            sourceIndex: null,
            element: null,
            clone: null,
            startX: 0,
            startY: 0,
            offsetX: 0,
            offsetY: 0
        };
        this.featureIcons = [
            { value: 'fa-certificate', label: 'Certificate' },
            { value: 'fa-infinity', label: 'Lifetime Access' },
            { value: 'fa-download', label: 'Downloadable' },
            { value: 'fa-question-circle', label: 'Quizzes' },
            { value: 'fa-tasks', label: 'Assignments' },
            { value: 'fa-video', label: 'Video Content' },
            { value: 'fa-users', label: 'Community' },
            { value: 'fa-mobile-alt', label: 'Mobile Access' },
            { value: 'fa-headset', label: 'Support' },
            { value: 'fa-shield-alt', label: 'Guarantee' },
            { value: 'fa-book', label: 'Reading Material' },
            { value: 'fa-code', label: 'Coding Exercises' },
            { value: 'fa-project-diagram', label: 'Projects' },
            { value: 'fa-comments', label: 'Discussion' },
            { value: 'fa-clock', label: 'Flexible Schedule' },
            { value: 'fa-globe', label: 'Online Access' },
            { value: 'fa-star', label: 'Premium Content' },
            { value: 'fa-graduation-cap', label: 'Graduation' },
            { value: 'fa-trophy', label: 'Achievement' },
            { value: 'fa-bolt', label: 'Quick Learning' },
            { value: 'fa-check-circle', label: 'General' }
        ];
        this.init();
    }

    getDefaultData() {
        return {
            title: '', subtitle: '', shortDescription: '', category: '', subcategory: '', tags: [],
            level: 'intermediate', language: 'en', duration: '', visibility: 'public', fullDescription: '',
            sections: [],
            outcomes: [],
            prerequisites: [],
            targetAudience: [],
            features: [],
            priceType: 'paid', price: 49.99, discountPrice: '',
            thumbnail: null, promoVideo: '', attachments: [], attachment_files: [], courseTrailer: '',
            seoTitle: '', seoDescription: '',
            version: '1.0', versionNotes: '', versionHistory: [],
            status: 'draft', reviewStatus: 'not_submitted', lastUpdated: new Date()
        };
    }

    async init() {
        this.bindGlobalEvents();

        await this.loadCourseMetadata();
        this.renderStep(this.currentStep);
        this.hideLoader();
    }

    async loadCourseMetadata() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/courses/metadata/",
                {
                    method: "GET",
                }
            );

            if (response.ok) {
                const metadata = await response.json();
                this.courseLanguages = metadata.languages;
                this.courseLevels = metadata.levels;
            }
        } catch (error) {
            console.error("Error loading course metadata:", error);
            this.courseLanguages = [{ value: 'en', label: 'English' }];
            this.courseLevels = [
                { value: 'beginner', label: 'Beginner' },
                { value: 'intermediate', label: 'Intermediate' },
                { value: 'advanced', label: 'Advanced' },
                { value: 'all_levels', label: 'All Levels' }
            ];
        }
    }

    bindGlobalEvents() {
        document.getElementById('hamburgerBtn')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.toggle('open'));
        document.getElementById('mobileMenuBtn')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('appSidebar')?.classList.toggle('open'); });
        document.getElementById('sidebarOverlay')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.remove('open'));
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => { e.stopPropagation(); document.getElementById('userDropdown')?.classList.toggle('open'); });
        document.addEventListener('click', (e) => { if (!e.target.closest('.user-menu-wrapper')) document.getElementById('userDropdown')?.classList.remove('open'); });

        document.getElementById('prevStepBtn')?.addEventListener('click', () => this.prevStep());
        document.getElementById('nextStepBtn')?.addEventListener('click', () => this.nextStep());
        document.getElementById('saveDraftBtn')?.addEventListener('click', () => this.saveDraft(true));

        document.querySelectorAll('.progress-step').forEach(step => {
            step.addEventListener('click', () => {
                const s = parseInt(step.dataset.step);
                this.goToStep(s);
            });
        });

        document.getElementById('lessonModalClose')?.addEventListener('click', () => this.closeLessonModal());
        document.getElementById('lessonModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeLessonModal();
        });
        document.getElementById('lessonModalSave')?.addEventListener('click', () => this.saveLessonContent());
        document.getElementById('lessonModalCancel')?.addEventListener('click', () => this.closeLessonModal());

        document.addEventListener('mousemove', (e) => this._onMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onMouseUp(e));
        document.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
        document.addEventListener('touchend', (e) => this._onTouchEnd(e));

        const stepContent = document.getElementById('stepContent');
        if (stepContent) {
            stepContent.addEventListener('mousedown', (e) => {
                const handle = e.target.closest('.drag-handle');
                if (!handle) return;

                e.preventDefault();
                e.stopPropagation();

                const dragType = handle.dataset.dragType;

                if (dragType === 'section') {
                    const sectionBlock = handle.closest('.section-block');
                    if (sectionBlock) {
                        const sectionIndex = parseInt(sectionBlock.dataset.section);
                        this._startDrag(e, handle, 'section', { sourceSection: sectionIndex }, sectionBlock);
                    }
                } else if (dragType === 'lesson') {
                    const lessonItem = handle.closest('.lesson-item');
                    if (lessonItem) {
                        const sectionIndex = parseInt(lessonItem.dataset.section);
                        const lessonIndex = parseInt(lessonItem.dataset.lesson);
                        this._startDrag(e, handle, 'lesson', { sourceSection: sectionIndex, sourceLesson: lessonIndex }, lessonItem);
                    }
                } else if (dragType === 'prerequisite') {
                    const prereqItem = handle.closest('.prereq-item');
                    if (prereqItem) {
                        const index = parseInt(prereqItem.dataset.index);
                        this._startDrag(e, handle, 'prerequisites', { sourceIndex: index }, prereqItem);
                    }
                } else if (dragType === 'audience') {
                    const audienceItem = handle.closest('.audience-item');
                    if (audienceItem) {
                        const index = parseInt(audienceItem.dataset.index);
                        this._startDrag(e, handle, 'targetAudience', { sourceIndex: index }, audienceItem);
                    }
                }
            });

            stepContent.addEventListener('touchstart', (e) => {
                const handle = e.target.closest('.drag-handle');
                if (!handle) return;

                e.preventDefault();

                const dragType = handle.dataset.dragType;
                const touch = e.touches[0];

                if (dragType === 'prerequisite') {
                    const prereqItem = handle.closest('.prereq-item');
                    if (prereqItem) {
                        const index = parseInt(prereqItem.dataset.index);
                        this._startDrag(touch, handle, 'prerequisites', { sourceIndex: index }, prereqItem);
                    }
                } else if (dragType === 'audience') {
                    const audienceItem = handle.closest('.audience-item');
                    if (audienceItem) {
                        const index = parseInt(audienceItem.dataset.index);
                        this._startDrag(touch, handle, 'targetAudience', { sourceIndex: index }, audienceItem);
                    }
                } else if (dragType === 'section') {
                    const sectionBlock = handle.closest('.section-block');
                    if (sectionBlock) {
                        const sectionIndex = parseInt(sectionBlock.dataset.section);
                        this._startDrag(touch, handle, 'section', { sourceSection: sectionIndex }, sectionBlock);
                    }
                } else if (dragType === 'lesson') {
                    const lessonItem = handle.closest('.lesson-item');
                    if (lessonItem) {
                        const sectionIndex = parseInt(lessonItem.dataset.section);
                        const lessonIndex = parseInt(lessonItem.dataset.lesson);
                        this._startDrag(touch, handle, 'lesson', { sourceSection: sectionIndex, sourceLesson: lessonIndex }, lessonItem);
                    }
                }
            }, { passive: false });
        }
    }

    renderStep(step, skipCollect = false) {
        this.currentStep = step;
        if (!skipCollect) {
            this.collectStepData();
        }
        this.updateProgressUI();
        this.updateNavigationButtons();

        const container = document.getElementById('stepContent');
        if (!container) return;

        switch (step) {
            case 1: container.innerHTML = this.renderBasicInfo(); this.loadCourseCategories(); this.bindFeatureEvents(); break;
            case 2: container.innerHTML = this.renderCurriculum(); break;
            case 3: container.innerHTML = this.renderOutcomes(); break;
            case 4: container.innerHTML = this.renderPrerequisites(); break;
            case 5: container.innerHTML = this.renderTargetAudience(); break;
            case 6: container.innerHTML = this.renderPricing(); break;
            case 7: container.innerHTML = this.renderMedia(); break;
            case 8: container.innerHTML = this.renderPublishing(); break;
        }

        this.bindStepEvents(step);
        document.getElementById('stepContent').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    async loadCourseCategories() {
        const select = document.getElementById("courseCategory");
        const subcategorySelect = document.getElementById("courseSubcategory");

        if (!select) return;

        // Save current selections before rebuilding
        const currentCategory = this.courseData.category;
        const currentSubcategory = this.courseData.subcategory;

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/courses/categories/",
                { method: "GET" }
            );

            if (!response.ok) {
                throw new Error("Failed to load categories.");
            }

            const data = await response.json();
            this.courseCategories = Array.isArray(data) ? data : (data.results || []);

            select.innerHTML = `
                <option value="">Select category</option>
                ${this.courseCategories.map(category => `<option value="${category.slug}" ${category.slug === currentCategory ? 'selected' : ''}>${category.name}</option>`).join("")}
            `;

            select.addEventListener("change", (event) => {
                this.loadSubcategoriesForCategory(event.target.value);
            });

            // If there was a previously selected category, load its subcategories
            if (currentCategory) {
                await this.loadSubcategoriesForCategory(currentCategory, currentSubcategory);
            } else {
                if (subcategorySelect) {
                    subcategorySelect.innerHTML = `<option value="">Select subcategory</option>`;
                    subcategorySelect.disabled = true;
                }
            }

        } catch (error) {
            console.error("Error loading categories:", error);
            select.innerHTML = `<option value="">Unable to load categories</option>`;
        }
    }

    async loadSubcategoriesForCategory(categorySlug, selectedSubcategory = "") {
        const subcategorySelect = document.getElementById("courseSubcategory");

        if (!subcategorySelect) return;

        if (!categorySlug) {
            subcategorySelect.innerHTML = `<option value="">Select subcategory</option>`;
            subcategorySelect.disabled = true;
            return;
        }

        this.courseData.category = categorySlug;
        this.courseData.subcategory = selectedSubcategory || '';

        const selectedCategory = this.courseCategories.find(cat => cat.slug === categorySlug);

        if (!selectedCategory) {
            subcategorySelect.innerHTML = `<option value="">No subcategories available</option>`;
            subcategorySelect.disabled = true;
            return;
        }

        const subcategories = selectedCategory.subcategories || [];

        if (subcategories.length === 0) {
            subcategorySelect.innerHTML = `<option value="">No subcategories available</option>`;
            subcategorySelect.disabled = true;
            return;
        }

        subcategorySelect.innerHTML = `
            <option value="">Select subcategory</option>
            ${subcategories.map(subcategory => `<option value="${subcategory.slug}" ${subcategory.slug === selectedSubcategory ? 'selected' : ''}>${subcategory.name}</option>`).join("")}
        `;
        subcategorySelect.disabled = false;

        subcategorySelect.addEventListener("change", (event) => {
            this.courseData.subcategory = event.target.value;
        });
    }

    renderBasicInfo() {
        const d = this.courseData;

        const languageOptions = this.courseLanguages.length > 0
            ? this.courseLanguages.map(lang => {
                const value = lang.value || lang.code || lang;
                const label = lang.label || lang.name || value;
                return `<option value="${value}" ${d.language===value?'selected':''}>${label}</option>`;
            }).join('')
            : `<option value="en" ${d.language==='en'?'selected':''}>English</option>`;

        const levelOptions = this.courseLevels.length > 0
            ? this.courseLevels.map(level => {
                const value = level.value || level.code || level;
                const label = level.label || level.name || value;
                return `<option value="${value}" ${d.level===value?'selected':''}>${label}</option>`;
            }).join('')
            : `<option value="beginner" ${d.level==='beginner'?'selected':''}>Beginner</option>
               <option value="intermediate" ${d.level==='intermediate'?'selected':''}>Intermediate</option>
               <option value="advanced" ${d.level==='advanced'?'selected':''}>Advanced</option>
               <option value="all_levels" ${d.level==='all_levels'?'selected':''}>All Levels</option>`;

        const activeFeatures = (d.features || []).filter(f => !f.deleted);

        const featureIconOptions = this.featureIcons.map(icon =>
            `<option value="${icon.value}">${icon.label}</option>`
        ).join('');

        return `
            <h2>Basic Information</h2><p class="step-description">Tell students what your course is about</p>
            <div class="form-group"><label>Course Title <span class="required">*</span></label><input type="text" id="courseTitle" class="form-input" value="${this.esc(d.title)}" placeholder="e.g. Complete Python Bootcamp 2026"></div>
            <div class="form-group"><label>Subtitle</label><input type="text" id="courseSubtitle" class="form-input" value="${this.esc(d.subtitle)}" placeholder="A catchy subtitle for your course"></div>
            <div class="form-group"><label>Short Description <span class="required">*</span></label><input type="text" id="shortDesc" class="form-input" value="${this.esc(d.shortDescription)}" placeholder="A concise summary" maxlength="300"><span class="char-count" id="shortDescCount">${(d.shortDescription||'').length}/300</span></div>
            <div class="form-row">
                <div class="form-group"><label>Category <span class="required">*</span></label><select id="courseCategory" class="form-select"><option value="">Select category</option></select></div>
                <div class="form-group"><label>Subcategory</label><select id="courseSubcategory" class="form-select"><option value="">Select subcategory</option></select></div>
            </div>
            <div class="form-group"><label>Tags</label><div class="tags-container" id="tagsContainer">${(d.tags||[]).map((t,i)=>`<span class="tag-chip">${this.esc(t)}<button class="tag-chip-remove" data-index="${i}"><i class="fas fa-times"></i></button></span>`).join('')}</div><div class="add-tag-row"><input type="text" id="tagInput" class="form-input" placeholder="Add a tag..."><button class="add-btn" id="addTagBtn"><i class="fas fa-plus"></i> Add</button></div></div>
            <div class="form-row-3">
                <div class="form-group"><label>Level <span class="required">*</span></label><select id="courseLevel" class="form-select"><option value="">Select level</option>${levelOptions}</select></div>
                <div class="form-group"><label>Language <span class="required">*</span></label><select id="courseLanguage" class="form-select"><option value="">Select language</option>${languageOptions}</select></div>
                <div class="form-group"><label>Duration (hours)</label><input type="text" id="courseDuration" class="form-input" value="${this.esc(d.duration)}" placeholder="e.g. 42"></div>
            </div>
            <div class="form-row"><div class="form-group"><label>Visibility</label><select id="courseVisibility" class="form-select"><option value="public" ${d.visibility==='public'?'selected':''}>Public</option><option value="private" ${d.visibility==='private'?'selected':''}>Private</option><option value="unlisted" ${d.visibility==='unlisted'?'selected':''}>Unlisted</option></select></div></div>
            <div class="form-group">
                <label>Course Features</label>
                <div class="features-list" id="featuresList">
                    ${activeFeatures.map((f,i)=>`
                        <div class="feature-item" style="display:flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid var(--color-gray-200);border-radius:8px;margin-bottom:8px;background:var(--color-gray-50);">
                            <i class="fas ${this.esc(f.icon || 'fa-check-circle')}" style="color:var(--color-primary-500);font-size:1.1rem;"></i>
                            <span style="flex:1;font-size:0.85rem;">${this.esc(f.text)}</span>
                            <button class="feature-remove" data-index="${i}" style="background:none;border:none;color:var(--color-gray-400);cursor:pointer;font-size:1rem;"><i class="fas fa-times"></i></button>
                        </div>
                    `).join('')}
                    ${activeFeatures.length===0?'<p style="color:var(--color-gray-400);font-size:0.78rem;text-align:center;padding:8px;">No features added yet</p>':''}
                </div>
                <div class="add-feature-row" style="display:flex;gap:10px;margin-top:10px;align-items:flex-end;">
                    <div class="form-group" style="margin-bottom:0;max-width:200px;">
                        <label style="font-size:0.78rem;">Icon</label>
                        <select id="newFeatureIcon" class="form-select" style="padding:8px 12px;">${featureIconOptions}</select>
                    </div>
                    <div class="form-group" style="margin-bottom:0;flex:1;">
                        <label style="font-size:0.78rem;">Feature Text</label>
                        <input type="text" id="newFeatureText" class="form-input" placeholder="e.g. Certificate of Completion">
                    </div>
                    <button class="add-btn" id="addFeatureBtn" style="margin-bottom:0;"><i class="fas fa-plus"></i> Add</button>
                </div>
            </div>
            <div class="form-group"><label>Full Description</label><textarea id="fullDescription" class="form-input form-textarea" placeholder="Describe your course in detail...">${this.esc(d.fullDescription)}</textarea></div>
        `;
    }

    bindFeatureEvents() {
        document.getElementById('addFeatureBtn')?.addEventListener('click', () => this.addFeature());
        document.getElementById('newFeatureText')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.addFeature();
        });
        document.querySelectorAll('.feature-remove').forEach(b => {
            b.addEventListener('click', () => this.removeFeature(parseInt(b.dataset.index)));
        });
    }

    addFeature() {
        const textInput = document.getElementById('newFeatureText');
        const iconSelect = document.getElementById('newFeatureIcon');
        const text = textInput?.value?.trim();
        const icon = iconSelect?.value || 'fa-check-circle';
        if (!text) return;
        this.courseData.features.push({ text: text, icon: icon, deleted: false });
        if (textInput) textInput.value = '';
        if (iconSelect) iconSelect.value = 'fa-check-circle';
        this.renderStep(1);
        this.showToast('Feature added');
    }

    removeFeature(i) {
        this.courseData.features.splice(i, 1);
        this.renderStep(1);
        this.showToast('Feature removed');
    }

    renderCurriculum() {
        let html = '<h2>Curriculum Builder</h2><p class="step-description">Organize your course content. Drag to reorder. Click a lesson to add content.</p><div class="curriculum-builder" id="curriculumBuilder">';
        this.courseData.sections.forEach((section, si) => {
            const lessonCount = section.lessons.length;
            html += `
                <div class="section-block" data-section="${si}">
                    <div class="section-header" onclick="createCoursePage.toggleSectionCollapse(${si})">
                        <span class="section-drag drag-handle" data-drag-type="section" data-section="${si}"><i class="fas fa-grip-vertical"></i></span>
                        <div class="section-header-info">
                            <input type="text" value="${this.esc(section.title)}" class="section-title-input" data-section="${si}" placeholder="Section title" onclick="event.stopPropagation();">
                            <div class="section-meta-row">
                                <textarea class="section-meta-input description-textarea" data-section="${si}" placeholder="Description" onclick="event.stopPropagation();" rows="2">${this.esc(section.description||'')}</textarea>
                                <input type="text" value="${this.esc(section.duration||'')}" class="section-meta-input duration" data-section="${si}" placeholder="Duration" onclick="event.stopPropagation();">
                            </div>
                        </div>
                        <div class="section-actions">
                            <span style="font-size:0.72rem;color:var(--color-gray-400);">${lessonCount} lessons</span>
                            <i class="fas fa-chevron-down collapse-icon" id="collapseIcon${si}"></i>
                            <button class="section-action-btn" onclick="event.stopPropagation();createCoursePage.duplicateSection(${si})" title="Duplicate"><i class="fas fa-copy"></i></button>
                            <button class="section-action-btn delete" onclick="event.stopPropagation();createCoursePage.removeSection(${si})" title="Delete"><i class="fas fa-trash-alt"></i></button>
                        </div>
                    </div>
                    <div class="section-lessons" id="sectionLessons${si}" data-section="${si}">
                        ${section.lessons.map((lesson, li) => this.renderLessonItem(lesson, si, li)).join('')}
                        <button class="add-lesson-btn" data-section="${si}" onclick="event.stopPropagation();createCoursePage.addLesson(${si})"><i class="fas fa-plus"></i> Add Lesson</button>
                    </div>
                </div>`;
        });
        html += '</div><button class="add-section-btn" id="addSectionBtn"><i class="fas fa-plus"></i> Add Section</button>';
        return html;
    }

    renderLessonItem(lesson, si, li) {
        const hasContent = lesson.type === 'video' ? !!(lesson.content?.videoUrl || lesson.content?.videoFile || lesson.content?.textContent) :
                         lesson.type === 'article' ? !!lesson.content?.text :
                         lesson.type === 'file' ? !!(lesson.content?.fileUrl || lesson.content?.file) :
                         lesson.type === 'quiz' ? !!(lesson.content?.questions?.length) :
                         lesson.type === 'assignment' ? !!lesson.content?.instructions :
                         lesson.type === 'external' ? !!lesson.content?.url : false;
        const typeLabels = { video: 'Video', article: 'Article', file: 'FILE', quiz: 'Quiz', assignment: 'Assignment'};
        const typeOptions = ['video', 'article', 'file', 'quiz', 'assignment'];
        const hasAttachments = (lesson.content?.attachments?.length > 0);
        const hasCaptions = (lesson.content?.captions?.length > 0);
        const criteriaType = lesson.completion_criteria?.criteria_type || 'manual';
        const criteriaLabels = {
            manual: 'Manual',
            watch_video: 'Watch Video',
            read_article: 'Read Article',
            pass_quiz: 'Pass Quiz',
            submit_assignment: 'Submit Assignment'
        };
        const criteriaIcons = {
            manual: 'fa-check',
            watch_video: 'fa-play',
            read_article: 'fa-book',
            pass_quiz: 'fa-question-circle',
            submit_assignment: 'fa-tasks'
        };
        return `
            <div class="lesson-item" data-section="${si}" data-lesson="${li}">
                <span class="lesson-drag drag-handle" data-drag-type="lesson" data-section="${si}" data-lesson="${li}"><i class="fas fa-grip-vertical"></i></span>
                <span class="lesson-type-icon ${lesson.type}"><i class="fas fa-${lesson.type==='video'?'play':lesson.type==='article'||lesson.type==='file'?'file-lines':lesson.type==='quiz'?'circle-question':lesson.type==='assignment'?'tasks':lesson.type==='external'?'link':'code'}"></i></span>
                <span class="lesson-title-display" data-section="${si}" data-lesson="${li}">${this.esc(lesson.title)}</span>
                <i class="fas ${hasContent?'fa-check-circle lesson-content-indicator has-content':'fa-circle lesson-content-indicator no-content'}"></i>
                ${hasAttachments ? '<i class="fas fa-paperclip" style="color:var(--color-gray-400);font-size:0.7rem;" title="Has attachments"></i>' : ''}
                ${hasCaptions ? '<i class="fas fa-closed-captioning" style="color:var(--color-gray-400);font-size:0.7rem;margin-left:2px;" title="Has captions"></i>' : ''}
                <span class="lesson-preview-badge ${lesson.preview?'preview-enabled':'preview-disabled'}">${lesson.preview?'Preview':'No Preview'}</span>
                <span class="lesson-published-badge ${lesson.published?'published':'unpublished'}">${lesson.published?'Pub':'Unpub'}</span>
                <span class="completion-criteria-badge" title="Completion: ${criteriaLabels[criteriaType] || criteriaType}">
                    <i class="fas ${criteriaIcons[criteriaType] || 'fa-check'}" style="margin-right:2px;"></i>
                    ${criteriaLabels[criteriaType] || criteriaType}
                </span>
                <select class="lesson-type-select" data-section="${si}" data-lesson="${li}" onchange="event.stopPropagation();createCoursePage.changeLessonType(${si},${li},this.value)">
                    ${typeOptions.map(t => `<option value="${t}" ${lesson.type===t?'selected':''} ${t==='live_session'||t==='coding_exercise'?'disabled':''}>${typeLabels[t]}</option>`).join('')}
                </select>
                <span class="lesson-item-actions">
                    <button class="lesson-edit-btn" data-section="${si}" data-lesson="${li}" title="Edit content" onclick="event.stopPropagation();createCoursePage.openLessonModal(${si},${li})"><i class="fas fa-pen"></i></button>
                    <button class="section-action-btn" onclick="event.stopPropagation();createCoursePage.duplicateLesson(${si},${li})" title="Duplicate"><i class="fas fa-copy"></i></button>
                    <button class="section-action-btn delete" data-section="${si}" data-lesson="${li}" title="Delete" onclick="event.stopPropagation();createCoursePage.removeLesson(${si},${li})"><i class="fas fa-times"></i></button>
                </span>
            </div>`;
    }

    renderOutcomes() {
        return `<h2>Learning Outcomes</h2><p class="step-description">What will students learn from your course?</p><div class="outcomes-list" id="outcomesList">${this.courseData.outcomes.map((o,i)=>`<div class="outcome-item"><i class="fas fa-check-circle"></i><span>${this.esc(o)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newOutcome" class="form-input" placeholder="Add a learning outcome..."><button class="add-btn" id="addOutcomeBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    renderPrerequisites() {
        return `<h2>Prerequisites</h2><p class="step-description">What should students know before taking this course? Drag to reorder.</p><div class="prereq-list" id="prereqList">${this.courseData.prerequisites.map((p,i)=>`<div class="prereq-item" data-index="${i}"><span class="drag-handle" data-drag-type="prerequisite" data-index="${i}"><i class="fas fa-grip-vertical"></i></span><span>${this.esc(p)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newPrereq" class="form-input" placeholder="Add a prerequisite..."><button class="add-btn" id="addPrereqBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    renderTargetAudience() {
        return `<h2>Target Audience</h2><p class="step-description">Who is this course for? Drag to reorder.</p><div class="audience-list" id="audienceList">${this.courseData.targetAudience.map((a,i)=>`<div class="audience-item" data-index="${i}"><span class="drag-handle" data-drag-type="audience" data-index="${i}"><i class="fas fa-grip-vertical"></i></span><span>${this.esc(a)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newAudience" class="form-input" placeholder="Add target audience..."><button class="add-btn" id="addAudienceBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    renderPricing() {
        const d = this.courseData;
        return `<h2>Pricing</h2><p class="step-description">Set the price for your course</p><div class="pricing-toggle" id="pricingToggle"><button class="pricing-option ${d.priceType==='free'?'active':''}" data-type="free">Free</button><button class="pricing-option ${d.priceType==='paid'?'active':''}" data-type="paid">Paid</button></div><div id="pricingFields" style="${d.priceType==='free'?'display:none;':''}"><div class="form-row"><div class="form-group"><label>Price (USD) <span class="required">*</span></label><input type="number" id="coursePrice" class="form-input" value="${d.price||''}" placeholder="49.99" step="0.01" min="0"></div><div class="form-group"><label>Discount Price (optional)</label><input type="number" id="discountPrice" class="form-input" value="${d.discountPrice||''}" placeholder="39.99" step="0.01" min="0"></div></div></div>`;
    }

    renderMedia() {
        const d = this.courseData;
        return `<h2>Media & SEO</h2><p class="step-description">Upload a thumbnail, trailer, and optimize for search engines</p>
            <div class="form-group"><label>Course Thumbnail</label><div class="thumbnail-upload ${d.thumbnailPreview?'has-image':''}" id="thumbnailUpload" onclick="document.getElementById('thumbnailInput').click()">${d.thumbnailPreview ? `<img src="${d.thumbnailPreview}" alt="Thumbnail preview">` : '<div class="upload-placeholder"><i class="fas fa-image"></i><p>Click to upload thumbnail</p><small>Recommended: 1280x720px · Max 2MB</small></div>'}</div><input type="file" id="thumbnailInput" accept="image/*" style="display:none;" onchange="createCoursePage.handleThumbnail(this.files[0])"></div>
            <div class="form-group"><label>Course Trailer URL</label><input type="url" id="courseTrailer" class="form-input" value="${this.esc(d.courseTrailer)}" placeholder="https://youtube.com/watch?v=..."></div>
            <div class="form-group"><label>Promo Video URL</label><input type="url" id="promoVideo" class="form-input" value="${this.esc(d.promoVideo)}" placeholder="https://youtube.com/watch?v=..."></div>
            <div class="form-group"><label>Course Attachments</label><div id="attachmentsList">${(d.attachments||[]).map((a,i)=>`<div class="prereq-item"><i class="fas fa-paperclip"></i><span>${this.esc(a.name||a)}</span><button class="outcome-remove" data-index="${i}" data-type="attachment"><i class="fas fa-times"></i></button></div>`).join('')}${(d.attachments||[]).length===0?'<p style="color:var(--color-gray-400);font-size:0.78rem;text-align:center;padding:8px;">No attachments</p>':''}</div><button class="add-btn" id="addAttachmentBtn"><i class="fas fa-plus"></i> Add Attachment</button><input type="file" id="attachmentInput" style="display:none;" multiple></div>
            <div class="form-row"><div class="form-group"><label>SEO Title</label><input type="text" id="seoTitle" class="form-input" value="${this.esc(d.seoTitle)}" placeholder="Course title for search engines" maxlength="70"></div><div class="form-group"><label>SEO Description</label><input type="text" id="seoDescription" class="form-input" value="${this.esc(d.seoDescription)}" placeholder="Meta description" maxlength="160"></div></div>`;
    }

    renderPublishing() {
        const checks = [
            { key: 'title', label: 'Course title added', done: !!this.courseData.title },
            { key: 'description', label: 'Description completed', done: !!this.courseData.shortDescription },
            { key: 'thumbnail', label: 'Thumbnail uploaded', done: !!this.courseData.thumbnail },
            { key: 'instructor', label: 'Instructor profile verified', done: true },
            { key: 'category', label: 'Category selected', done: !!this.courseData.category },
            { key: 'outcomes', label: 'Learning outcomes defined', done: this.courseData.outcomes.length > 0 },
            { key: 'language', label: 'Language set', done: !!this.courseData.language },
            { key: 'pricing', label: 'Pricing configured', done: !!(this.courseData.priceType === 'free' || this.courseData.price) },
            { key: 'lessons', label: 'At least 1 published lesson', done: this.courseData.sections.some(s => s.lessons.some(l => l.published)) },
        ];
        const allDone = checks.filter(c => c.key !== 'review').every(c => c.done);

        return `
        <h2>Publishing Checklist</h2>
        <p class="step-description">Review your course before publishing</p>
        <div style="background:var(--color-gray-50);border:1px solid var(--color-gray-200);border-radius:var(--radius-lg);padding:16px 18px;margin-bottom:18px;">
            <h3 style="font-size:0.9rem;font-weight:600;color:var(--color-gray-900);margin-bottom:2px;"><i class="fas fa-code-branch"></i> Initial Version</h3>
            <p style="font-size:0.78rem;color:var(--color-gray-500);margin-bottom:12px;">Your course will be published as version <strong>1.0</strong> by default. You can change this if needed.</p>
            <div class="form-row">
                <div class="form-group"><label>Version</label><input type="text" id="courseVersion" class="form-input" value="${this.courseData.version || '1.0'}" style="max-width:120px;"></div>
                <div class="form-group"><label>Version Notes (optional)</label><input type="text" id="versionNotes" class="form-input" value="${this.esc(this.courseData.versionNotes||'')}" placeholder="e.g. Initial release"></div>
            </div>
        </div>
        <div class="checklist">${checks.map(c => `<div class="checklist-item ${c.done?'completed':''}"><span class="checklist-icon"><i class="fas fa-${c.done?'check':'minus'}"></i></span><span class="checklist-text">${c.label}</span></div>`).join('')}</div>
        <div class="publish-actions">
            <button class="nav-btn outline" id="saveDraftPublishBtn"><i class="fas fa-save"></i> Save Draft</button>
            <button class="nav-btn primary" id="submitReviewPublishBtn" ${allDone?'':'disabled style="opacity:0.5;cursor:not-allowed;"'}><i class="fas fa-paper-plane"></i> Submit For Review</button>

        </div>`;
    }

    bindStepEvents(step) {
        if (step === 1) {
            document.getElementById('shortDesc')?.addEventListener('input', (e) => {
                const countEl = document.getElementById('shortDescCount');
                if (countEl) countEl.textContent = `${e.target.value.length}/300`;
            });
            document.getElementById('addTagBtn')?.addEventListener('click', () => this.addTag());
            document.getElementById('tagInput')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addTag();
            });
            document.querySelectorAll('.tag-chip-remove').forEach(b => b.addEventListener('click', () => {
                this.removeTag(parseInt(b.dataset.index));
            }));
        }

        if (step === 2) {
            document.getElementById('addSectionBtn')?.addEventListener('click', () => this.addSection());
            document.querySelectorAll('.lesson-edit-btn').forEach(b => {
                b.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openLessonModal(parseInt(b.dataset.section), parseInt(b.dataset.lesson));
                });
            });
            document.querySelectorAll('.lesson-title-display').forEach(span => {
                span.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openLessonModal(parseInt(span.dataset.section), parseInt(span.dataset.lesson));
                });
            });
            document.querySelectorAll('.section-title-input').forEach(inp => {
                inp.addEventListener('click', (e) => e.stopPropagation());
            });
            document.querySelectorAll('.section-meta-input.description-textarea').forEach(textarea => {
                textarea.addEventListener('click', (e) => e.stopPropagation());
                textarea.addEventListener('input', (e) => {
                    const si = parseInt(e.target.dataset.section);
                    if (!isNaN(si) && this.courseData.sections[si]) {
                        this.courseData.sections[si].description = e.target.value;
                    }
                });
            });
        }

        if (step === 3) {
            document.getElementById('addOutcomeBtn')?.addEventListener('click', () => this.addOutcome());
            document.getElementById('newOutcome')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addOutcome();
            });
            document.querySelectorAll('.outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removeOutcome(parseInt(b.dataset.index)));
            });
        }

        if (step === 4) {
            document.getElementById('addPrereqBtn')?.addEventListener('click', () => this.addPrerequisite());
            document.getElementById('newPrereq')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addPrerequisite();
            });
            document.querySelectorAll('#prereqList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removePrerequisite(parseInt(b.dataset.index)));
            });
        }

        if (step === 5) {
            document.getElementById('addAudienceBtn')?.addEventListener('click', () => this.addAudience());
            document.getElementById('newAudience')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addAudience();
            });
            document.querySelectorAll('#audienceList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removeAudience(parseInt(b.dataset.index)));
            });
        }

        if (step === 6) {
            document.querySelectorAll('.pricing-option').forEach(b => {
                b.addEventListener('click', () => {
                    document.querySelectorAll('.pricing-option').forEach(x => x.classList.remove('active'));
                    b.classList.add('active');
                    const pricingFields = document.getElementById('pricingFields');
                    if (pricingFields) pricingFields.style.display = b.dataset.type === 'free' ? 'none' : '';
                });
            });
        }

        if (step === 7) {
            document.getElementById('addAttachmentBtn')?.addEventListener('click', () => {
                document.getElementById('attachmentInput')?.click();
            });
            document.getElementById('attachmentInput')?.addEventListener('change', (e) => {
                if (e.target.files) {
                    if (!this.courseData.attachment_files) {
                        this.courseData.attachment_files = [];
                    }
                    for (let f of e.target.files) {
                        this.courseData.attachments = [...(this.courseData.attachments||[]), { name: f.name, size: f.size, type: f.type, lastModified: f.lastModified }];
                        this.courseData.attachment_files.push(f);
                    }
                    this.renderStep(7);
                }
            });
            document.querySelectorAll('#attachmentsList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => {
                    const index = parseInt(b.dataset.index);
                    this.courseData.attachments.splice(index, 1);
                    if (this.courseData.attachment_files && this.courseData.attachment_files[index]) {
                        this.courseData.attachment_files.splice(index, 1);
                    }
                    this.renderStep(7);
                });
            });
        }

        if (step === 8) {
            document.getElementById('saveDraftPublishBtn')?.addEventListener('click', () => this.saveDraft(true));
            document.getElementById('submitReviewPublishBtn')?.addEventListener('click', () => this.submitForReview());

        }
    }

    // CRITICAL FIX: Save current form data before re-rendering modal
    saveCurrentFormData() {
        if (!this.editingLesson) return;

        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson) return;

        const titleEl = document.getElementById('lessonTitle');
        if (titleEl) lesson.title = titleEl.value.trim() || lesson.title;

        const descEl = document.getElementById('lessonDesc');
        if (descEl) lesson.description = descEl.value.trim();

        const durEl = document.getElementById('lessonDuration');
        if (durEl) lesson.duration = durEl.value.trim();

        const prevEl = document.getElementById('lessonPreview');
        if (prevEl) lesson.preview = prevEl.value === '1';

        const pubEl = document.getElementById('lessonPublished');
        if (pubEl) lesson.published = pubEl.value === '1';

        if (lesson.type !== 'quiz' && lesson.type !== 'assignment') {
            this.saveCurrentCompletionCriteriaData();
        }

        if (lesson.type === 'video') {
            const videoFileInput = document.getElementById('lessonVideoFile');
            const videoUrlInput = document.getElementById('lessonVideoUrl');
            const videoTextInput = document.getElementById('lessonVideoText');
            const videoTranscriptInput = document.getElementById('lessonTranscript');
            const activeSource = document.querySelector('#videoSourceToggle .pricing-option.active');
            const videoSource = activeSource?.dataset?.source || 'file';

            if (!lesson.content) lesson.content = {};

            if (videoFileInput?.files[0]) {
                lesson.content.videoFile = videoFileInput.files[0];
                lesson.content.videoFileName = videoFileInput.files[0].name;
                lesson.content.videoSource = 'file';
            } else if (videoSource === 'url') {
                lesson.content.videoSource = 'url';
                lesson.content.videoUrl = videoUrlInput?.value || '';
            }

            if (videoTextInput) lesson.content.textContent = videoTextInput.value || '';
            if (videoTranscriptInput) lesson.content.transcript = videoTranscriptInput.value || '';
        }
    }

    saveCurrentQuizFormData() {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'quiz') return;

        const quizSettings = {
            instructions: document.getElementById('quizInstructions')?.value || '',
            passingScore: parseInt(document.getElementById('quizPassingScore')?.value) || 70,
            timeLimit: document.getElementById('quizTimeLimit')?.value ? parseInt(document.getElementById('quizTimeLimit').value) : null,
            maxAttempts: parseInt(document.getElementById('quizMaxAttempts')?.value) || 1,
            shuffleQuestions: document.getElementById('quizShuffleQuestions')?.checked || false,
            shuffleChoices: document.getElementById('quizShuffleChoices')?.checked || false,
            showCorrectAnswers: document.getElementById('quizShowCorrectAnswers')?.checked || false
        };

        const questions = [];
        document.querySelectorAll('.quiz-question-block').forEach(block => {
            const qi = parseInt(block.dataset.question);
            const text = block.querySelector('.quiz-question-text')?.value?.trim() || '';
            const questionType = block.querySelector('.quiz-question-type')?.value || 'single_choice';
            const difficulty = block.querySelector('.quiz-question-difficulty')?.value || 'medium';
            const points = parseInt(block.querySelector('.quiz-question-points')?.value) || 1;
            const estimatedTime = block.querySelector('.quiz-question-time')?.value ? parseInt(block.querySelector('.quiz-question-time').value) : null;
            const isRequired = block.querySelector('.quiz-question-required')?.checked !== false;
            const explanation = block.querySelector('.quiz-explanation')?.value || '';
            const order = qi + 1;

            let questionData = {
                text, question_type: questionType, difficulty, points,
                estimated_time: estimatedTime, is_required: isRequired,
                explanation, order
            };

            if (questionType === 'single_choice' || questionType === 'multiple_choice') {
                const options = Array.from(block.querySelectorAll('.quiz-option-text')).map(inp => inp.value || '');
                if (questionType === 'single_choice') {
                    const correctRadio = block.querySelector('.quiz-correct-input:checked');
                    questionData.correct = correctRadio ? parseInt(correctRadio.dataset.option) : 0;
                } else {
                    const checkedInputs = block.querySelectorAll('.quiz-correct-input:checked');
                    questionData.correct = Array.from(checkedInputs).map(inp => parseInt(inp.dataset.option));
                }
                questionData.options = options;
            } else if (questionType === 'true_false') {
                const correctSelect = block.querySelector('.quiz-true-false-correct');
                questionData.correct = correctSelect?.value === 'true';
            } else if (questionType === 'short_answer') {
                const answerInputs = block.querySelectorAll('.accepted-answer-input');
                questionData.accepted_answers = Array.from(answerInputs).map(inp => inp.value.trim()).filter(val => val !== '');
                if (questionData.accepted_answers.length === 0) {
                    questionData.accepted_answers = [''];
                }
            }

            questions.push(questionData);
        });

        lesson.content = {
            ...lesson.content,
            quizSettings,
            questions,
            attachments: lesson.content?.attachments || [],
            attachment_files: lesson.content?.attachment_files || []
        };

        if (!lesson.completion_criteria) lesson.completion_criteria = {};
        lesson.completion_criteria.criteria_type = 'pass_quiz';
        lesson.completion_criteria.quiz_passing_score = quizSettings.passingScore;
        lesson.completion_criteria.video_watch_percentage = null;
    }

    saveCurrentAssignmentFormData() {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'assignment') return;

        const assignmentData = {
            instructions: document.getElementById('assignmentInstructions')?.value || '',
            maxScore: parseInt(document.getElementById('assignmentMaxScore')?.value) || 100,
            dueDate: document.getElementById('assignmentDueDate')?.value || null,
            allowLateSubmission: document.getElementById('assignmentAllowLate')?.checked || false,
            maxAttempts: parseInt(document.getElementById('assignmentMaxAttempts')?.value) || 1,
            acceptedFileTypes: document.getElementById('assignmentAcceptedFileTypes')?.value || '',
            maxFileSizeMb: parseInt(document.getElementById('assignmentMaxFileSize')?.value) || 50
        };

        lesson.content = {
            ...lesson.content,
            ...assignmentData,
            attachments: lesson.content?.attachments || [],
            attachment_files: lesson.content?.attachment_files || []
        };

        if (!lesson.completion_criteria) lesson.completion_criteria = {};
        lesson.completion_criteria.criteria_type = 'submit_assignment';
        lesson.completion_criteria.video_watch_percentage = null;
        lesson.completion_criteria.quiz_passing_score = null;
    }

    saveCurrentCompletionCriteriaData() {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson) return;
        if (lesson.type === 'quiz' || lesson.type === 'assignment') return;

        const criteriaType = document.getElementById('lessonCompletionCriteriaType')?.value || 'manual';
        if (!lesson.completion_criteria) lesson.completion_criteria = {};
        lesson.completion_criteria.criteria_type = criteriaType;

        if (criteriaType === 'watch_video') {
            const watchPercentage = parseInt(document.getElementById('videoWatchPercentage')?.value) || 90;
            lesson.completion_criteria.video_watch_percentage = watchPercentage;
            lesson.completion_criteria.quiz_passing_score = null;
        } else if (criteriaType === 'pass_quiz') {
            const passingScore = parseInt(document.getElementById('quizPassingScoreCriteria')?.value) || 70;
            lesson.completion_criteria.quiz_passing_score = passingScore;
            lesson.completion_criteria.video_watch_percentage = null;
        } else {
            lesson.completion_criteria.video_watch_percentage = null;
            lesson.completion_criteria.quiz_passing_score = null;
        }
    }

    openLessonModal(si, li) {
        // CRITICAL FIX: Don't call collectStepData here - it interferes with lesson data
        const lesson = this.courseData.sections[si]?.lessons[li];
        if (!lesson) return;
        this.editingLesson = { sectionIndex: si, lessonIndex: li };
        document.getElementById('modalLessonTitle').textContent = lesson.title || 'Untitled Lesson';
        document.getElementById('modalLessonType').textContent = lesson.type.charAt(0).toUpperCase() + lesson.type.slice(1);

        const criteriaType = lesson.completion_criteria?.criteria_type || 'manual';
        const videoWatchPercentage = lesson.completion_criteria?.video_watch_percentage || 90;
        const quizPassingScore = lesson.completion_criteria?.quiz_passing_score || 70;

        let html = `
        <div class="form-group"><label>Lesson Title</label><input type="text" id="lessonTitle" class="form-input" value="${this.esc(lesson.title)}"></div>
        <div class="form-group"><label>Description</label><textarea id="lessonDesc" class="form-input form-textarea" rows="3">${this.esc(lesson.description||'')}</textarea></div>
        <div class="form-row"><div class="form-group"><label>Duration (min)</label><input type="number" id="lessonDuration" class="form-input" value="${this.esc(lesson.duration||'')}" min="1"></div><div class="form-group"><label>Preview Enabled</label><select id="lessonPreview" class="form-select"><option value="1" ${lesson.preview?'selected':''}>Yes</option><option value="0" ${!lesson.preview?'selected':''}>No</option></select></div></div>
        <div class="form-row"><div class="form-group"><label>Published</label><select id="lessonPublished" class="form-select"><option value="1" ${lesson.published?'selected':''}>Yes</option><option value="0" ${!lesson.published?'selected':''}>No</option></select></div></div>`;

        if (lesson.type !== 'quiz' && lesson.type !== 'assignment') {
            html += `
        <div class="form-group completion-criteria-section" style="background:var(--color-gray-50);border:1px solid var(--color-gray-200);border-radius:var(--radius-lg);padding:16px;margin-bottom:16px;">
            <label style="font-weight:600;display:block;margin-bottom:8px;"><i class="fas fa-check-circle"></i> Completion Criteria</label>
            <p style="font-size:0.78rem;color:var(--color-gray-500);margin-bottom:10px;">Define how students complete this lesson</p>
            <div class="form-group" style="margin-bottom:10px;">
                <label>Criteria Type</label>
                <select id="lessonCompletionCriteriaType" class="form-select" onchange="createCoursePage.toggleCompletionCriteriaFields()">
                    <option value="manual" ${criteriaType==='manual'?'selected':''}>Manual (student marks as complete)</option>
                    <option value="watch_video" ${criteriaType==='watch_video'?'selected':''}>Watch Video (percentage based)</option>
                    <option value="read_article" ${criteriaType==='read_article'?'selected':''}>Read Article (scroll to end)</option>
                    <option value="pass_quiz" ${criteriaType==='pass_quiz'?'selected':''}>Pass Quiz (score based)</option>
                    <option value="submit_assignment" ${criteriaType==='submit_assignment'?'selected':''}>Submit Assignment</option>
                </select>
            </div>
            <div id="videoWatchPercentageField" style="display:${criteriaType==='watch_video'?'block':'none'};">
                <div class="form-group" style="margin-bottom:10px;">
                    <label>Required Watch Percentage (%)</label>
                    <input type="number" id="videoWatchPercentage" class="form-input" value="${videoWatchPercentage}" min="1" max="100" placeholder="90">
                    <small style="color:var(--color-gray-400);display:block;margin-top:4px;">Student must watch this percentage of the video (1-100)</small>
                </div>
            </div>
            <div id="quizPassingScoreCriteriaField" style="display:${criteriaType==='pass_quiz'?'block':'none'};">
                <div class="form-group" style="margin-bottom:10px;">
                    <label>Required Passing Score (%)</label>
                    <input type="number" id="quizPassingScoreCriteria" class="form-input" value="${quizPassingScore}" min="0" max="100" placeholder="70">
                    <small style="color:var(--color-gray-400);display:block;margin-top:4px;">Student must score at least this percentage to pass (0-100)</small>
                </div>
            </div>
        </div>`;
        }

        if (lesson.type === 'video') {
            const isFileSource = lesson.content?.videoSource === 'file' || (!lesson.content?.videoSource && !lesson.content?.videoUrl);
            html += `
            <div class="form-group">
                <label>Video Source</label>
                <div class="pricing-toggle" id="videoSourceToggle" style="margin-bottom:0;">
                    <button class="pricing-option ${isFileSource ? 'active' : ''}" data-source="file" type="button">Upload File</button>
                    <button class="pricing-option ${!isFileSource ? 'active' : ''}" data-source="url" type="button">External URL</button>
                </div>
            </div>
            <div id="videoFileSection" style="${!isFileSource ? 'display:none;' : ''}">
                <div class="form-group" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:20px;text-align:center;margin-bottom:16px;">
                    <label style="font-weight:600;display:block;margin-bottom:8px;">Upload Video File</label>
                    <input type="file" id="lessonVideoFile" accept="video/*" class="form-input" style="max-width:300px;margin:0 auto;">
                    ${lesson.content?.videoFileName ? `<p style="margin-top:8px;font-size:0.82rem;color:var(--color-success);"><i class="fas fa-check-circle"></i> Uploaded: ${this.esc(lesson.content.videoFileName)}</p>` : ''}
                    <small style="color:var(--color-gray-400);display:block;margin-top:4px;">Max 2GB · MP4, WebM, MOV</small>
                </div>
            </div>
            <div id="videoUrlSection" style="${isFileSource ? 'display:none;' : ''}">
                <div class="form-group"><label>Video URL</label><input type="url" id="lessonVideoUrl" class="form-input" value="${this.esc(lesson.content?.videoUrl||'')}" placeholder="https://youtube.com/watch?v=... or https://vimeo.com/..."><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Supports YouTube, Vimeo, and direct MP4 links</small></div>
            </div>
            <div class="form-group"><label>Text Content / Description Below Video</label><textarea id="lessonVideoText" class="form-input form-textarea" rows="6" placeholder="Additional text content shown below the video...">${this.esc(lesson.content?.textContent||'')}</textarea></div>
            <div class="form-group"><label>Transcript</label><textarea id="lessonTranscript" class="form-input form-textarea" rows="6" placeholder="Enter video transcript here...">${this.esc(lesson.content?.transcript||'')}</textarea><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Optional. Transcript helps with accessibility and search.</small></div>
            <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--color-gray-200);" id="captionsSection">
                <div class="form-group"><label><i class="fas fa-closed-captioning"></i> Captions / Subtitles</label><p style="font-size:0.78rem;color:var(--color-gray-500);margin-bottom:10px;">Add subtitle files in VTT or SRT format for different languages.</p></div>
                <div id="captionsList">
                    ${(lesson.content?.captions || []).map((cap, i) => `
                        <div class="caption-item-card" data-caption-index="${i}" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--color-gray-200);border-radius:8px;margin-bottom:8px;background:var(--color-gray-50);">
                            <i class="fas fa-closed-captioning" style="color:var(--color-primary-500);font-size:1.1rem;"></i>
                            <div style="flex:1;min-width:0;">
                                <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
                                    <span style="font-weight:600;font-size:0.85rem;color:var(--color-gray-800);">${this.esc(cap.label || cap.language)}</span>
                                    <span style="font-size:0.7rem;padding:2px 8px;background:var(--color-primary-100);color:var(--color-primary-700);border-radius:9999px;">${cap.language.toUpperCase()}</span>
                                    ${cap.isDefault ? '<span style="font-size:0.7rem;padding:2px 8px;background:#D1FAE5;color:#065F46;border-radius:9999px;">Default</span>' : ''}
                                </div>
                                <div style="font-size:0.75rem;color:var(--color-gray-500);">${cap.fileName ? `<i class="fas fa-file-alt"></i> ${this.esc(cap.fileName)} · ${cap.fileFormat?.toUpperCase() || 'VTT'}` : 'No file uploaded'}</div>
                            </div>
                            <div style="display:flex;gap:4px;">
                                ${!cap.isDefault ? `<button class="section-action-btn" onclick="createCoursePage.setDefaultCaption(${i})" title="Set as default" style="color:var(--color-success);"><i class="fas fa-check-circle"></i></button>` : ''}
                                <button class="section-action-btn delete" onclick="createCoursePage.removeCaption(${i})" title="Remove caption"><i class="fas fa-trash-alt"></i></button>
                            </div>
                        </div>
                    `).join('')}
                    ${(lesson.content?.captions || []).length === 0 ? '<p style="color:var(--color-gray-400);font-size:0.82rem;text-align:center;padding:16px;">No captions added yet</p>' : ''}
                </div>
                <div id="addCaptionForm" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:18px;margin-top:10px;">
                    <h4 style="font-size:0.85rem;font-weight:600;color:var(--color-gray-700);margin-bottom:12px;">Add New Caption</h4>
                    <div class="form-row" style="margin-bottom:10px;">
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Language Code *</label><select id="captionLanguage" class="form-input" style="padding:8px 12px;"><option value="en">English (en)</option><option value="es">Spanish (es)</option><option value="fr">French (fr)</option><option value="de">German (de)</option><option value="zh">Chinese (zh)</option><option value="ja">Japanese (ja)</option><option value="ko">Korean (ko)</option><option value="ar">Arabic (ar)</option><option value="pt">Portuguese (pt)</option><option value="ru">Russian (ru)</option><option value="it">Italian (it)</option><option value="other">Other...</option></select></div>
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Label *</label><input type="text" id="captionLabel" class="form-input" placeholder="e.g. English, Spanish" style="padding:8px 12px;"></div>
                    </div>
                    <div class="form-row" style="margin-bottom:10px;">
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Caption File * (.vtt or .srt)</label><input type="file" id="captionFileInput" accept=".vtt,.srt" class="form-input" style="padding:8px 12px;"></div>
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Format</label><select id="captionFormat" class="form-input" style="padding:8px 12px;"><option value="vtt">WebVTT (.vtt)</option><option value="srt">SubRip (.srt)</option></select></div>
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><label style="display:flex;align-items:center;gap:6px;font-size:0.8rem;color:var(--color-gray-600);cursor:pointer;"><input type="checkbox" id="captionIsDefault" style="accent-color:var(--color-primary-600);">Set as default caption</label></div>
                    <button class="add-btn" id="saveCaptionBtn" style="width:100%;"><i class="fas fa-plus"></i> Add Caption</button>
                </div>
            </div>`;
        } else if (lesson.type === 'article') {
            html += `<div class="form-group"><label>Article Content <span class="required">*</span></label><textarea id="lessonArticleText" class="form-input form-textarea" rows="14" placeholder="Write your article content here...">${this.esc(lesson.content?.text||'')}</textarea></div>`;
        } else if (lesson.type === 'file') {
            html += `<div class="form-group"><label>FILE URL</label><input type="url" id="lessonPdfUrl" class="form-input" value="${this.esc(lesson.content?.fileUrl||'')}" placeholder="https://example.com/document.pdf"><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Link to an externally hosted FILE file</small></div>
            <div class="form-group" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:20px;text-align:center;margin-bottom:16px;"><label style="font-weight:600;display:block;margin-bottom:8px;">Or Upload FILE File</label><input type="file" id="lessonFile" accept=".pdf,application/pdf" class="form-input" style="max-width:300px;margin:0 auto;">${lesson.content?.fileName ? `<p style="margin-top:8px;font-size:0.82rem;color:var(--color-success);"><i class="fas fa-check-circle"></i> Uploaded: ${this.esc(lesson.content.fileName)}</p>` : ''}<small style="color:var(--color-gray-400);display:block;margin-top:4px;">Max 50MB · FILE format only</small></div>`;
        } else if (lesson.type === 'quiz') {
            html += this.renderQuizContent(lesson);
        } else if (lesson.type === 'assignment') {
            html += this.renderAssignmentContent(lesson);
        } else if (lesson.type === 'external') {
            html += `<div class="form-group"><label>External URL</label><input type="url" id="lessonExternalUrl" class="form-input" value="${this.esc(lesson.content?.url||'')}" placeholder="https://..."></div>`;
        }

        const attachments = lesson.content?.attachments || [];
        html += `
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--color-gray-200);">
            <div class="form-group"><label><i class="fas fa-paperclip"></i> Lesson Attachments</label>
                <div id="lessonAttachmentsList">
                    ${attachments.map((a,i)=>`
                        <div class="prereq-item" style="margin-bottom:6px;display:flex;align-items:center;gap:8px;">
                            <i class="fas fa-paperclip"></i>
                            <div style="flex:1;min-width:0;">
                                <span style="display:block;font-size:0.85rem;">${this.esc(a.name||a)}</span>
                                <span style="font-size:0.7rem;color:var(--color-gray-500);">
                                    ${a.size ? this.formatFileSize(a.size) : ''}
                                    ${a.type ? ` · ${a.type}` : ''}
                                </span>
                            </div>
                            <button class="outcome-remove" data-index="${i}" data-type="lesson-attachment"><i class="fas fa-times"></i></button>
                        </div>
                    `).join('')}
                    ${attachments.length===0?'<p style="color:var(--color-gray-400);font-size:0.78rem;text-align:center;padding:8px;">No attachments yet</p>':''}
                </div>
                <button class="add-btn" id="addLessonAttachmentBtn"><i class="fas fa-plus"></i> Add Attachment</button>
                <input type="file" id="lessonAttachmentInput" style="display:none;" multiple>
            </div>
        </div>`;

        document.getElementById('lessonContentArea').innerHTML = html;
        document.getElementById('lessonModalOverlay').style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (lesson.type === 'video') {
            this.bindVideoEvents(lesson);
        } else if (lesson.type === 'quiz') {
            this.bindQuizEvents(lesson);
        } else if (lesson.type === 'assignment') {
            this.bindAssignmentEvents(lesson);
        }

        this.bindAttachmentEvents(lesson);
    }

    toggleCompletionCriteriaFields() {
        const criteriaType = document.getElementById('lessonCompletionCriteriaType')?.value || 'manual';
        const videoWatchField = document.getElementById('videoWatchPercentageField');
        const quizPassingField = document.getElementById('quizPassingScoreCriteriaField');
        if (videoWatchField) videoWatchField.style.display = criteriaType === 'watch_video' ? 'block' : 'none';
        if (quizPassingField) quizPassingField.style.display = criteriaType === 'pass_quiz' ? 'block' : 'none';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    renderQuizContent(lesson) {
        const quizSettings = lesson.content?.quizSettings || {
            instructions: '', passingScore: 70, timeLimit: null, maxAttempts: 1,
            shuffleQuestions: false, shuffleChoices: false, showCorrectAnswers: true
        };
        const questions = lesson.content?.questions || [];

        let html = `
        <div style="background:var(--color-gray-50);border:1px solid var(--color-gray-200);border-radius:var(--radius-lg);padding:16px;margin-bottom:20px;">
            <h4 style="font-size:0.9rem;font-weight:600;color:var(--color-gray-800);margin-bottom:12px;"><i class="fas fa-cog"></i> Quiz Settings</h4>
            <div class="form-group"><label>Quiz Instructions</label><textarea id="quizInstructions" class="form-input form-textarea" rows="3" placeholder="Enter instructions for students...">${this.esc(quizSettings.instructions)}</textarea></div>
            <div class="form-row">
                <div class="form-group"><label>Passing Score (%)</label><input type="number" id="quizPassingScore" class="form-input" value="${quizSettings.passingScore}" min="0" max="100" placeholder="70"><small style="color:var(--color-gray-400);">Required score to pass (0-100)</small></div>
                <div class="form-group"><label>Time Limit (minutes)</label><input type="number" id="quizTimeLimit" class="form-input" value="${quizSettings.timeLimit || ''}" min="0" placeholder="Leave empty for unlimited"><small style="color:var(--color-gray-400);">Leave empty for unlimited time</small></div>
            </div>
            <div class="form-row"><div class="form-group"><label>Maximum Attempts</label><input type="number" id="quizMaxAttempts" class="form-input" value="${quizSettings.maxAttempts}" min="0" placeholder="1"><small style="color:var(--color-gray-400);">Set to 0 for unlimited attempts</small></div></div>
            <div class="form-row" style="margin-top:12px;">
                <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" id="quizShuffleQuestions" ${quizSettings.shuffleQuestions ? 'checked' : ''} style="accent-color:var(--color-primary-600);"> Shuffle Questions</label></div>
                <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" id="quizShuffleChoices" ${quizSettings.shuffleChoices ? 'checked' : ''} style="accent-color:var(--color-primary-600);"> Shuffle Choices</label></div>
                <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" id="quizShowCorrectAnswers" ${quizSettings.showCorrectAnswers ? 'checked' : ''} style="accent-color:var(--color-primary-600);"> Show Correct Answers</label></div>
            </div>
        </div>
        <div style="border-top:2px solid var(--color-primary-100);padding-top:16px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <h4 style="font-size:0.9rem;font-weight:600;color:var(--color-gray-800);"><i class="fas fa-question-circle"></i> Questions (${questions.length})</h4>
                <div style="font-size:0.78rem;color:var(--color-gray-500);">Total Points: <strong id="quizTotalPoints">${this.calculateTotalPoints(questions)}</strong></div>
            </div>
            <div class="quiz-questions-container" id="quizQuestionsContainer">
                ${questions.length === 0 ? '<p style="color:var(--color-gray-400);text-align:center;padding:20px;">No questions yet. Add your first question below.</p>' : ''}
                ${questions.map((q, qi) => this.renderQuizQuestion(q, qi)).join('')}
            </div>
            <button class="add-section-btn" id="addQuizQuestionBtn" style="margin-top:12px;"><i class="fas fa-plus"></i> Add Question</button>
        </div>`;
        return html;
    }

    renderAssignmentContent(lesson) {
        const assignmentData = {
            instructions: lesson.content?.instructions || '',
            maxScore: lesson.content?.maxScore || 100,
            dueDate: lesson.content?.dueDate || '',
            allowLateSubmission: lesson.content?.allowLateSubmission || false,
            maxAttempts: lesson.content?.maxAttempts !== undefined ? lesson.content?.maxAttempts : 1,
            acceptedFileTypes: lesson.content?.acceptedFileTypes || '',
            maxFileSizeMb: lesson.content?.maxFileSizeMb || 50
        };

        let html = `
        <div style="background:var(--color-gray-50);border:1px solid var(--color-gray-200);border-radius:var(--radius-lg);padding:16px;margin-bottom:20px;">
            <h4 style="font-size:0.9rem;font-weight:600;color:var(--color-gray-800);margin-bottom:12px;"><i class="fas fa-tasks"></i> Assignment Settings</h4>
            <div class="form-group"><label>Instructions <span class="required">*</span></label><textarea id="assignmentInstructions" class="form-input form-textarea" rows="6" placeholder="Describe the assignment requirements, submission guidelines, and any special instructions...">${this.esc(assignmentData.instructions)}</textarea><small style="color:var(--color-gray-400);">Provide clear instructions for students</small></div>
            <div class="form-row">
                <div class="form-group"><label>Maximum Score <span class="required">*</span></label><input type="number" id="assignmentMaxScore" class="form-input" value="${assignmentData.maxScore}" min="1" placeholder="100"><small style="color:var(--color-gray-400);">Must be greater than 0</small></div>
                <div class="form-group"><label>Due Date</label><input type="datetime-local" id="assignmentDueDate" class="form-input" value="${assignmentData.dueDate ? assignmentData.dueDate.replace(' ', 'T').substring(0, 16) : ''}"><small style="color:var(--color-gray-400);">Leave empty for no due date</small></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Maximum Attempts</label><input type="number" id="assignmentMaxAttempts" class="form-input" value="${assignmentData.maxAttempts}" min="0" placeholder="1"><small style="color:var(--color-gray-400);">Set to 0 for unlimited attempts</small></div>
                <div class="form-group"><label>Maximum File Size (MB)</label><input type="number" id="assignmentMaxFileSize" class="form-input" value="${assignmentData.maxFileSizeMb}" min="1" placeholder="50"><small style="color:var(--color-gray-400);">Must be greater than 0</small></div>
            </div>
            <div class="form-group"><label>Accepted File Types</label><input type="text" id="assignmentAcceptedFileTypes" class="form-input" value="${this.esc(assignmentData.acceptedFileTypes)}" placeholder="e.g. pdf,docx,zip,pptx"><small style="color:var(--color-gray-400);">Comma-separated list. Leave empty to allow any file type.</small></div>
            <div class="form-group" style="margin-top:12px;"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" id="assignmentAllowLate" ${assignmentData.allowLateSubmission ? 'checked' : ''} style="accent-color:var(--color-primary-600);"> Allow Late Submission</label><small style="color:var(--color-gray-400);display:block;margin-top:4px;">If enabled, students can submit after the due date</small></div>
            <div style="margin-top:12px;padding:12px;background:var(--color-primary-50);border-radius:8px;border:1px solid var(--color-primary-100);">
                <h5 style="font-size:0.8rem;font-weight:600;color:var(--color-primary-700);margin-bottom:6px;"><i class="fas fa-lightbulb"></i> Common File Type Suggestions</h5>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    <button class="file-type-suggestion-btn" data-types="pdf" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">PDF Document</button>
                    <button class="file-type-suggestion-btn" data-types="docx,doc" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">Word Document</button>
                    <button class="file-type-suggestion-btn" data-types="zip,rar" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">Archive Files</button>
                    <button class="file-type-suggestion-btn" data-types="jpg,png,gif" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">Images</button>
                    <button class="file-type-suggestion-btn" data-types="py,js,html,css" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">Code Files</button>
                    <button class="file-type-suggestion-btn" data-types="pptx,ppt" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">PowerPoint</button>
                    <button class="file-type-suggestion-btn" data-types="xlsx,xls" style="font-size:0.72rem;padding:4px 10px;background:white;border:1px solid var(--color-primary-200);border-radius:4px;cursor:pointer;color:var(--color-primary-700);">Excel</button>
                </div>
            </div>
        </div>`;
        return html;
    }

    renderQuizQuestion(q, qi) {
        const questionType = q.question_type || 'single_choice';
        const difficulty = q.difficulty || 'medium';
        const points = q.points || 1;
        const isRequired = q.is_required !== undefined ? q.is_required : true;
        const estimatedTime = q.estimated_time || '';
        let options = q.options || ['', '', '', ''];
        const acceptedAnswers = q.accepted_answers || [''];

        let optionsHtml = '';
        let correctAnswerHtml = '';

        if (questionType === 'single_choice' || questionType === 'multiple_choice') {
            if (!options || options.length < 2) options = ['', ''];
            optionsHtml = `
                <div class="quiz-options" data-question="${qi}">
                    <label style="font-size:0.8rem;font-weight:600;color:var(--color-gray-700);margin-bottom:6px;display:block;">${questionType === 'multiple_choice' ? 'Choices (select multiple correct answers)' : 'Choices (select one correct answer)'}</label>
                    ${options.map((opt, oi) => `
                        <div class="quiz-option-row">
                            <input type="${questionType === 'multiple_choice' ? 'checkbox' : 'radio'}" name="correct_q${qi}" class="quiz-correct-input" ${questionType === 'single_choice' && q.correct === oi ? 'checked' : ''} ${questionType === 'multiple_choice' && Array.isArray(q.correct) && q.correct.includes(oi) ? 'checked' : ''} data-option="${oi}">
                            <input type="text" class="form-input quiz-option-text" value="${this.esc(opt)}" placeholder="Option ${oi+1}" data-option="${oi}">
                            <button class="section-action-btn delete remove-option-btn" data-question="${qi}" data-option="${oi}" title="Remove option" style="display:${options.length > 2 ? 'inline-flex' : 'none'};"><i class="fas fa-times"></i></button>
                        </div>
                    `).join('')}
                    <button class="add-option-btn" data-question="${qi}" style="margin-top:8px;font-size:0.82rem;color:var(--color-primary-600);background:none;border:none;cursor:pointer;"><i class="fas fa-plus"></i> Add Option</button>
                </div>`;
        } else if (questionType === 'true_false') {
            correctAnswerHtml = `
                <div class="form-group"><label style="font-size:0.8rem;font-weight:600;color:var(--color-gray-700);">Correct Answer</label><select class="form-input quiz-true-false-correct" data-question="${qi}"><option value="true" ${q.correct === true || q.correct === 'true' ? 'selected' : ''}>True</option><option value="false" ${q.correct === false || q.correct === 'false' ? 'selected' : ''}>False</option></select></div>`;
        } else if (questionType === 'short_answer') {
            let displayAnswers = acceptedAnswers;
            if (!displayAnswers || displayAnswers.length === 0) displayAnswers = [''];
            correctAnswerHtml = `
                <div class="form-group"><label style="font-size:0.8rem;font-weight:600;color:var(--color-gray-700);">Accepted Answers</label><div class="accepted-answers-container" data-question="${qi}">
                    ${displayAnswers.map((ans, ai) => `
                        <div class="accepted-answer-row" style="display:flex;gap:8px;margin-bottom:6px;">
                            <input type="text" class="form-input accepted-answer-input" value="${this.esc(ans)}" placeholder="Acceptable answer" data-answer="${ai}">
                            <button class="section-action-btn delete remove-accepted-answer-btn" data-question="${qi}" data-answer="${ai}" title="Remove"><i class="fas fa-times"></i></button>
                        </div>
                    `).join('')}
                </div><button class="add-accepted-answer-btn" data-question="${qi}" style="margin-top:6px;font-size:0.82rem;color:var(--color-primary-600);background:none;border:none;cursor:pointer;"><i class="fas fa-plus"></i> Add Accepted Answer</button></div>`;
        }

        return `
            <div class="quiz-question-block" data-question="${qi}" style="background:white;border:1px solid var(--color-gray-200);border-radius:8px;padding:16px;margin-bottom:12px;">
                <div class="quiz-question-header" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span class="drag-handle" style="cursor:grab;color:var(--color-gray-400);"><i class="fas fa-grip-vertical"></i></span>
                        <span class="quiz-question-number" style="font-weight:600;color:var(--color-primary-600);">Question ${qi + 1}</span>
                        <span style="font-size:0.7rem;padding:2px 8px;background:var(--color-${difficulty === 'easy' ? 'success' : difficulty === 'medium' ? 'warning' : 'danger'}-100);color:var(--color-${difficulty === 'easy' ? 'success' : difficulty === 'medium' ? 'warning' : 'danger'}-700);border-radius:9999px;">${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}</span>
                    </div>
                    <button class="section-action-btn delete remove-question-btn" data-question="${qi}" title="Remove question"><i class="fas fa-trash-alt"></i></button>
                </div>
                <div class="form-group"><label>Question Text <span class="required">*</span></label><textarea class="form-input form-textarea quiz-question-text" rows="2" placeholder="Enter your question">${this.esc(q.text||'')}</textarea></div>
                <div class="form-row">
                    <div class="form-group"><label>Question Type</label><select class="form-select quiz-question-type" data-question="${qi}"><option value="single_choice" ${questionType === 'single_choice' ? 'selected' : ''}>Single Choice</option><option value="multiple_choice" ${questionType === 'multiple_choice' ? 'selected' : ''}>Multiple Choice</option><option value="true_false" ${questionType === 'true_false' ? 'selected' : ''}>True / False</option><option value="short_answer" ${questionType === 'short_answer' ? 'selected' : ''}>Short Answer</option></select></div>
                    <div class="form-group"><label>Difficulty</label><select class="form-select quiz-question-difficulty" data-question="${qi}"><option value="easy" ${difficulty === 'easy' ? 'selected' : ''}>Easy</option><option value="medium" ${difficulty === 'medium' ? 'selected' : ''}>Medium</option><option value="hard" ${difficulty === 'hard' ? 'selected' : ''}>Hard</option></select></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Points</label><input type="number" class="form-input quiz-question-points" value="${points}" min="1" data-question="${qi}"></div>
                    <div class="form-group"><label>Estimated Time (seconds)</label><input type="number" class="form-input quiz-question-time" value="${estimatedTime}" min="0" placeholder="Optional" data-question="${qi}"></div>
                </div>
                <div class="form-group"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" class="quiz-question-required" ${isRequired ? 'checked' : ''} data-question="${qi}" style="accent-color:var(--color-primary-600);"> Required Question</label></div>
                ${optionsHtml}
                ${correctAnswerHtml}
                <div class="form-group" style="margin-top:8px;"><label>Explanation (shown after answering)</label><textarea class="form-input form-textarea quiz-explanation" rows="2" placeholder="Explain the correct answer...">${this.esc(q.explanation||'')}</textarea></div>
            </div>`;
    }

    calculateTotalPoints(questions) {
        return questions.reduce((sum, q) => sum + (parseInt(q.points) || 1), 0);
    }

    bindQuizEvents(lesson) {
        document.getElementById('addQuizQuestionBtn')?.addEventListener('click', () => {
            this.saveCurrentFormData();
            this.saveCurrentQuizFormData();
            this.addQuizQuestion();
        });
        document.querySelectorAll('.quiz-question-type').forEach(select => {
            select.addEventListener('change', (e) => {
                const qi = parseInt(e.target.dataset.question);
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                this.changeQuestionType(qi, e.target.value);
            });
        });
        document.querySelectorAll('.remove-question-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                this.removeQuizQuestion(parseInt(btn.dataset.question));
            });
        });
        document.querySelectorAll('.add-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                const qi = parseInt(btn.dataset.question);
                this.addQuizOption(qi);
            });
        });
        document.querySelectorAll('.remove-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                const qi = parseInt(btn.dataset.question);
                const oi = parseInt(btn.dataset.option);
                this.removeQuizOption(qi, oi);
            });
        });
        document.querySelectorAll('.add-accepted-answer-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                const qi = parseInt(btn.dataset.question);
                this.addAcceptedAnswer(qi);
            });
        });
        document.querySelectorAll('.remove-accepted-answer-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.saveCurrentFormData();
                this.saveCurrentQuizFormData();
                const qi = parseInt(btn.dataset.question);
                const ai = parseInt(btn.dataset.answer);
                this.removeAcceptedAnswer(qi, ai);
            });
        });
        document.querySelectorAll('.quiz-question-points').forEach(input => {
            input.addEventListener('change', () => this.updateTotalPoints());
        });
    }

    bindAssignmentEvents(lesson) {
        document.querySelectorAll('.file-type-suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const types = btn.dataset.types;
                const input = document.getElementById('assignmentAcceptedFileTypes');
                if (input) {
                    const currentTypes = input.value.split(',').map(t => t.trim()).filter(t => t);
                    const newTypes = types.split(',').map(t => t.trim());
                    newTypes.forEach(type => {
                        if (!currentTypes.includes(type)) currentTypes.push(type);
                    });
                    input.value = currentTypes.join(',');
                }
            });
        });
        const dueDateInput = document.getElementById('assignmentDueDate');
        if (dueDateInput) {
            dueDateInput.addEventListener('change', (e) => {
                const selectedDate = e.target.value;
                if (selectedDate) {
                    const dateObj = new Date(selectedDate);
                    if (dateObj.getHours() === 0 && dateObj.getMinutes() === 0) {
                        const now = new Date();
                        const year = dateObj.getFullYear();
                        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                        const day = String(dateObj.getDate()).padStart(2, '0');
                        const hours = String(now.getHours()).padStart(2, '0');
                        const minutes = String(now.getMinutes()).padStart(2, '0');
                        e.target.value = `${year}-${month}-${day}T${hours}:${minutes}`;
                    }
                }
            });
            dueDateInput.addEventListener('focus', function handler(e) {
                if (!dueDateInput.value) {
                    const now = new Date();
                    const year = now.getFullYear();
                    const month = String(now.getMonth() + 1).padStart(2, '0');
                    const day = String(now.getDate()).padStart(2, '0');
                    const hours = String(now.getHours()).padStart(2, '0');
                    const minutes = String(now.getMinutes()).padStart(2, '0');
                    dueDateInput.min = `${year}-${month}-${day}T${hours}:${minutes}`;
                }
                dueDateInput.removeEventListener('focus', handler);
            });
        }
    }

    bindVideoEvents(lesson) {
        document.querySelectorAll('#videoSourceToggle .pricing-option').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#videoSourceToggle .pricing-option').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const source = btn.dataset.source;
                document.getElementById('videoFileSection').style.display = source === 'file' ? '' : 'none';
                if (source === 'file') {
                    document.getElementById('lessonVideoUrl').value = "";
                } else if (source === 'url') {
                    document.getElementById('lessonVideoFile').value = "";
                }
                document.getElementById('videoUrlSection').style.display = source === 'url' ? '' : 'none';
            });
        });
        document.getElementById('saveCaptionBtn')?.addEventListener('click', () => {
            this.saveCurrentFormData();
            this.saveCaption();
        });
        document.getElementById('captionLanguage')?.addEventListener('change', (e) => {
            const labelMap = { 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'pt': 'Portuguese', 'ru': 'Russian', 'it': 'Italian' };
            const label = document.getElementById('captionLabel');
            if (label && !label.value) label.value = labelMap[e.target.value] || '';
        });
        document.getElementById('captionFileInput')?.addEventListener('change', (e) => {
            const file = e.target.files?.[0];
            if (file) {
                const ext = file.name.split('.').pop().toLowerCase();
                const formatSelect = document.getElementById('captionFormat');
                if (formatSelect && (ext === 'vtt' || ext === 'srt')) formatSelect.value = ext;
            }
        });
    }

    bindAttachmentEvents(lesson) {
        const lessonType = lesson.type;
        document.getElementById('addLessonAttachmentBtn')?.addEventListener('click', () => document.getElementById('lessonAttachmentInput')?.click());
        document.getElementById('lessonAttachmentInput')?.addEventListener('change', (e) => {
            if (e.target.files && this.editingLesson) {
                this.saveCurrentFormData();
                if (lessonType === 'quiz') {
                    this.saveCurrentQuizFormData();
                } else if (lessonType === 'assignment') {
                    this.saveCurrentAssignmentFormData();
                }
                const currentLesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
                if (currentLesson) {
                    if (!currentLesson.content) currentLesson.content = {};
                    if (!currentLesson.content.attachments) currentLesson.content.attachments = [];
                    if (!currentLesson.content.attachment_files) currentLesson.content.attachment_files = [];
                    for (let f of e.target.files) {
                        currentLesson.content.attachments.push({
                            name: f.name,
                            size: f.size,
                            type: f.type,
                            lastModified: f.lastModified
                        });
                        currentLesson.content.attachment_files.push(f);
                    }
                    this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
                }
            }
        });
        document.querySelectorAll('#lessonAttachmentsList .outcome-remove').forEach(b => {
            b.addEventListener('click', () => {
                if (this.editingLesson) {
                    this.saveCurrentFormData();
                    if (lessonType === 'quiz') {
                        this.saveCurrentQuizFormData();
                    } else if (lessonType === 'assignment') {
                        this.saveCurrentAssignmentFormData();
                    }
                    const currentLesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
                    if (currentLesson?.content?.attachments) {
                        const index = parseInt(b.dataset.index);
                        currentLesson.content.attachments.splice(index, 1);
                        if (currentLesson.content.attachment_files && currentLesson.content.attachment_files[index]) {
                            currentLesson.content.attachment_files.splice(index, 1);
                        }
                        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
                    }
                }
            });
        });
    }

    closeLessonModal() {
        if (this.editingLesson) {
            const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
            if (lesson) {
                if (lesson.type === 'quiz') {
                    this.saveCurrentQuizFormData();
                } else if (lesson.type === 'assignment') {
                    this.saveCurrentAssignmentFormData();
                } else {
                    this.saveCurrentCompletionCriteriaData();
                }
            }
        }
        document.getElementById('lessonModalOverlay').style.display = 'none';
        document.body.style.overflow = '';
        this.editingLesson = null;
    }

    saveLessonContent() {
        if (!this.editingLesson) return;
        const { sectionIndex, lessonIndex } = this.editingLesson;
        const lesson = this.courseData.sections[sectionIndex]?.lessons[lessonIndex];
        if (!lesson) return;

        // CRITICAL FIX: First save ALL form data
        this.saveCurrentFormData();

        const titleEl = document.getElementById('lessonTitle');
        if (titleEl) lesson.title = titleEl.value.trim() || 'Untitled Lesson';
        const descEl = document.getElementById('lessonDesc');
        if (descEl) lesson.description = descEl.value.trim();
        const durEl = document.getElementById('lessonDuration');
        if (durEl) lesson.duration = durEl.value.trim();
        const prevEl = document.getElementById('lessonPreview');
        if (prevEl) lesson.preview = prevEl.value === '1';
        const pubEl = document.getElementById('lessonPublished');
        if (pubEl) lesson.published = pubEl.value === '1';

        if (lesson.type !== 'quiz' && lesson.type !== 'assignment') {
            this.saveCurrentCompletionCriteriaData();
        }

        const existingAttachments = lesson.content?.attachments || [];
        const existingAttachmentFiles = lesson.content?.attachment_files || [];

        if (lesson.type === 'video') {
            const activeSource = document.querySelector('#videoSourceToggle .pricing-option.active');
            const videoSource = activeSource?.dataset?.source || 'file';
            const videoFileInput = document.getElementById('lessonVideoFile');
            let videoFile = lesson.content?.videoFile || null;
            let videoFileName = lesson.content?.videoFileName || '';
            if (videoFileInput?.files[0]) {
                videoFile = videoFileInput.files[0];
                videoFileName = videoFileInput.files[0].name;
            }
            const existingCaptions = lesson.content?.captions || [];
            lesson.content = {
                videoSource,
                videoUrl: document.getElementById('lessonVideoUrl')?.value || '',
                videoFile,
                videoFileName,
                textContent: document.getElementById('lessonVideoText')?.value || '',
                transcript: document.getElementById('lessonTranscript')?.value || '',
                captions: existingCaptions,
                duration: lesson.duration,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        } else if (lesson.type === 'article') {
            lesson.content = {
                text: document.getElementById('lessonArticleText')?.value || '',
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        } else if (lesson.type === 'file') {
            const fileInput = document.getElementById('lessonFile');
            let file = lesson.content?.file || null;
            let fileName = lesson.content?.fileName || '';
            if (fileInput?.files[0]) {
                file = fileInput.files[0];
                fileName = fileInput.files[0].name;
            }
            lesson.content = {
                fileUrl: document.getElementById('lessonPdfUrl')?.value || '',
                file,
                fileName,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        } else if (lesson.type === 'quiz') {
            this.saveCurrentQuizFormData();
        } else if (lesson.type === 'assignment') {
            this.saveCurrentAssignmentFormData();
        } else if (lesson.type === 'external') {
            lesson.content = {
                url: document.getElementById('lessonExternalUrl')?.value || '',
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }

        this.closeLessonModal();
        this.renderStep(2, true); // Skip collectStepData to preserve lesson data
        this.showToast('Lesson content saved ✓');
    }

    saveCaption() {
        if (!this.editingLesson) return;
        this.saveCurrentFormData();
        const language = document.getElementById('captionLanguage')?.value;
        const label = document.getElementById('captionLabel')?.value?.trim();
        const fileInput = document.getElementById('captionFileInput');
        const format = document.getElementById('captionFormat')?.value || 'vtt';
        const isDefault = document.getElementById('captionIsDefault')?.checked || false;
        if (!language) { this.showToast('Please select a language'); return; }
        if (!label) { this.showToast('Please enter a label'); return; }
        if (!fileInput?.files?.[0]) { this.showToast('Please select a caption file'); return; }
        const file = fileInput.files[0];
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'vtt' && ext !== 'srt') { this.showToast('Only .vtt and .srt files are supported'); return; }
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'video') return;
        if (!lesson.content) lesson.content = {};
        if (!lesson.content.captions) lesson.content.captions = [];
        if (isDefault) lesson.content.captions.forEach(cap => cap.isDefault = false);
        const autoDefault = lesson.content.captions.length === 0 ? true : isDefault;
        if (autoDefault) lesson.content.captions.forEach(cap => cap.isDefault = false);
        lesson.content.captions.push({
            language,
            label,
            fileName: file.name,
            fileSize: file.size,
            file: file,
            fileFormat: format,
            isDefault: autoDefault
        });
        this.showToast('Caption added');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeCaption(index) {
        if (!this.editingLesson) return;
        this.saveCurrentFormData();
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.captions) return;
        const wasDefault = lesson.content.captions[index]?.isDefault;
        lesson.content.captions.splice(index, 1);
        if (wasDefault && lesson.content.captions.length > 0) lesson.content.captions[0].isDefault = true;
        this.showToast('Caption removed');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    setDefaultCaption(index) {
        if (!this.editingLesson) return;
        this.saveCurrentFormData();
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.captions) return;
        lesson.content.captions.forEach((cap, i) => { cap.isDefault = (i === index); });
        this.showToast('Default caption updated');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    addQuizQuestion() {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'quiz') return;
        if (!lesson.content) lesson.content = {
            quizSettings: {
                instructions: '', passingScore: 70, timeLimit: null, maxAttempts: 1,
                shuffleQuestions: false, shuffleChoices: false, showCorrectAnswers: true
            },
            questions: [],
            attachments: [],
            attachment_files: []
        };
        if (!lesson.content.questions) lesson.content.questions = [];
        if (!lesson.content.quizSettings) lesson.content.quizSettings = {
            instructions: '', passingScore: 70, timeLimit: null, maxAttempts: 1,
            shuffleQuestions: false, shuffleChoices: false, showCorrectAnswers: true
        };

        lesson.content.questions.push({
            text: '',
            question_type: 'single_choice',
            options: ['', '', '', ''],
            correct: 0,
            explanation: '',
            difficulty: 'medium',
            points: 1,
            is_required: true,
            estimated_time: null,
            accepted_answers: [],
            order: lesson.content.questions.length + 1
        });

        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeQuizQuestion(index) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        lesson.content.questions.splice(index, 1);
        lesson.content.questions.forEach((q, i) => q.order = i + 1);
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    changeQuestionType(qi, newType) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;

        const question = lesson.content.questions[qi];
        if (!question) return;

        const oldText = question.text;
        const oldExplanation = question.explanation;
        const oldDifficulty = question.difficulty;
        const oldPoints = question.points;
        const oldIsRequired = question.is_required;
        const oldEstimatedTime = question.estimated_time;

        question.question_type = newType;
        question.text = oldText;
        question.explanation = oldExplanation;
        question.difficulty = oldDifficulty;
        question.points = oldPoints;
        question.is_required = oldIsRequired;
        question.estimated_time = oldEstimatedTime;

        if (newType === 'single_choice') {
            question.options = question.options || ['', '', '', ''];
            if (question.options.length < 2) question.options = ['', '', '', ''];
            question.correct = 0;
            question.accepted_answers = [];
        } else if (newType === 'multiple_choice') {
            question.options = question.options || ['', '', '', ''];
            if (question.options.length < 2) question.options = ['', '', '', ''];
            question.correct = [];
            question.accepted_answers = [];
        } else if (newType === 'true_false') {
            question.correct = true;
            question.options = [];
            question.accepted_answers = [];
        } else if (newType === 'short_answer') {
            question.accepted_answers = question.accepted_answers || [''];
            if (question.accepted_answers.length === 0) question.accepted_answers = [''];
            question.options = [];
            question.correct = null;
        }

        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    addQuizOption(qi) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        const question = lesson.content.questions[qi];
        if (!question) return;
        if (!question.options) question.options = [];
        question.options.push('');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeQuizOption(qi, oi) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        const question = lesson.content.questions[qi];
        if (!question || !question.options) return;
        if (question.options.length <= 2) {
            this.showToast('Minimum 2 options required');
            return;
        }
        question.options.splice(oi, 1);
        if (question.question_type === 'single_choice') {
            if (question.correct === oi) {
                question.correct = 0;
            } else if (question.correct > oi) {
                question.correct--;
            }
        } else if (question.question_type === 'multiple_choice' && Array.isArray(question.correct)) {
            question.correct = question.correct.filter(c => c !== oi).map(c => c > oi ? c - 1 : c);
        }
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    addAcceptedAnswer(qi) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        const question = lesson.content.questions[qi];
        if (!question) return;
        if (!question.accepted_answers) question.accepted_answers = [];
        question.accepted_answers.push('');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeAcceptedAnswer(qi, ai) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        const question = lesson.content.questions[qi];
        if (!question?.accepted_answers) return;
        question.accepted_answers.splice(ai, 1);
        if (question.accepted_answers.length === 0) {
            question.accepted_answers = [''];
        }
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    updateTotalPoints() {
        const totalEl = document.getElementById('quizTotalPoints');
        if (!totalEl || !this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        let total = 0;
        document.querySelectorAll('.quiz-question-points').forEach(input => {
            total += parseInt(input.value) || 1;
        });
        totalEl.textContent = total;
    }

    changeLessonType(si, li, newType) {
        const lesson = this.courseData.sections[si]?.lessons[li];
        if (!lesson) return;
        const oldAtt = lesson.content?.attachments || [];
        const oldAttFiles = lesson.content?.attachment_files || [];
        lesson.type = newType;

        let defaultCriteriaType = 'manual';
        let defaultVideoWatchPercentage = null;
        let defaultQuizPassingScore = null;

        if (newType === 'video') {
            defaultCriteriaType = 'watch_video';
            defaultVideoWatchPercentage = 90;
        } else if (newType === 'article') {
            defaultCriteriaType = 'read_article';
        } else if (newType === 'quiz') {
            defaultCriteriaType = 'pass_quiz';
            defaultQuizPassingScore = 70;
        } else if (newType === 'assignment') {
            defaultCriteriaType = 'submit_assignment';
        }

        lesson.completion_criteria = {
            criteria_type: defaultCriteriaType,
            video_watch_percentage: defaultVideoWatchPercentage,
            quiz_passing_score: defaultQuizPassingScore
        };

        if (newType === 'quiz') {
            lesson.content = {
                quizSettings: {
                    instructions: '', passingScore: 70, timeLimit: null, maxAttempts: 1,
                    shuffleQuestions: false, shuffleChoices: false, showCorrectAnswers: true
                },
                questions: [],
                attachments: oldAtt,
                attachment_files: oldAttFiles
            };
            lesson.completion_criteria.quiz_passing_score = 70;
        } else if (newType === 'assignment') {
            lesson.content = {
                instructions: '',
                maxScore: 100,
                dueDate: this.getCurrentDateTime(),
                allowLateSubmission: false,
                maxAttempts: 1,
                acceptedFileTypes: '',
                maxFileSizeMb: 50,
                attachments: oldAtt,
                attachment_files: oldAttFiles
            };
        } else if (newType === 'video') {
            lesson.content = {
                videoSource: 'file',
                videoUrl: '',
                videoFile: null,
                videoFileName: '',
                textContent: '',
                transcript: '',
                captions: [],
                attachments: oldAtt,
                attachment_files: oldAttFiles
            };
        } else {
            lesson.content = { attachments: oldAtt, attachment_files: oldAttFiles };
        }

        this.renderStep(2, true);
        this.showToast(`Lesson type changed to ${newType}`);
    }

    _startDrag(e, handle, type, data, element) {
        const rect = element.getBoundingClientRect();
        const clientX = e.clientX || e.pageX;
        const clientY = e.clientY || e.pageY;

        this.dragState = {
            active: true,
            type: type,
            sourceSection: data.sourceSection ?? null,
            sourceLesson: data.sourceLesson ?? null,
            sourceIndex: data.sourceIndex ?? null,
            element: element,
            clone: null,
            startX: clientX,
            startY: clientY,
            offsetX: clientX - rect.left,
            offsetY: clientY - rect.top
        };

        const clone = element.cloneNode(true);
        clone.classList.add('drag-clone');
        clone.style.position = 'fixed';
        clone.style.zIndex = '10000';
        clone.style.width = rect.width + 'px';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.pointerEvents = 'none';
        clone.style.opacity = '0.8';
        clone.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
        clone.style.backgroundColor = '#fff';
        document.body.appendChild(clone);

        this.dragState.clone = clone;
        element.classList.add('drag-source');
        document.body.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
    }

    _onMouseMove(e) {
        if (!this.dragState.active) return;

        const ds = this.dragState;
        const clientX = e.clientX;
        const clientY = e.clientY;

        if (ds.clone) {
            ds.clone.style.left = (clientX - ds.offsetX) + 'px';
            ds.clone.style.top = (clientY - ds.offsetY) + 'px';
        }

        const dx = clientX - ds.startX;
        const dy = clientY - ds.startY;
        if (Math.abs(dx) < 5 && Math.abs(dy) < 5) return;

        document.querySelectorAll('.drag-hover, .drag-hover-container').forEach(el => {
            el.classList.remove('drag-hover', 'drag-hover-container');
        });

        const elUnder = document.elementFromPoint(clientX, clientY);
        if (!elUnder) return;

        if (ds.type === 'section') {
            const sectionBlock = elUnder.closest('.section-block');
            if (sectionBlock && sectionBlock !== ds.element) {
                sectionBlock.classList.add('drag-hover');
            }
        } else if (ds.type === 'lesson') {
            const lessonItem = elUnder.closest('.lesson-item');
            const sectionLessons = elUnder.closest('.section-lessons');

            if (lessonItem && lessonItem !== ds.element) {
                const targetSection = parseInt(lessonItem.dataset.section);
                if (targetSection !== ds.sourceSection && sectionLessons) {
                    sectionLessons.classList.add('drag-hover-container');
                }
                lessonItem.classList.add('drag-hover');
            } else if (sectionLessons) {
                const targetSection = parseInt(sectionLessons.dataset.section);
                if (!isNaN(targetSection) && targetSection !== ds.sourceSection) {
                    sectionLessons.classList.add('drag-hover-container');
                }
            }
        } else if (ds.type === 'prerequisites') {
            const prereqItem = elUnder.closest('.prereq-item');
            if (prereqItem && prereqItem !== ds.element) {
                prereqItem.classList.add('drag-hover');
            }
        } else if (ds.type === 'targetAudience') {
            const audienceItem = elUnder.closest('.audience-item');
            if (audienceItem && audienceItem !== ds.element) {
                audienceItem.classList.add('drag-hover');
            }
        }
    }

    _onMouseUp(e) {
        if (!this.dragState.active) return;

        const ds = this.dragState;

        if (ds.clone) {
            ds.clone.remove();
        }

        if (ds.element) {
            ds.element.classList.remove('drag-source');
        }

        document.querySelectorAll('.drag-hover, .drag-hover-container').forEach(el => {
            el.classList.remove('drag-hover', 'drag-hover-container');
        });

        const clientX = e.clientX;
        const clientY = e.clientY;
        const elUnder = document.elementFromPoint(clientX, clientY);

        let reordered = false;

        if (ds.type === 'section') {
            const target = elUnder?.closest('.section-block');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.section);
                if (!isNaN(toIndex) && !isNaN(ds.sourceSection)) {
                    this._reorderSections(ds.sourceSection, toIndex);
                    reordered = true;
                }
            }
        } else if (ds.type === 'lesson') {
            const targetLesson = elUnder?.closest('.lesson-item');
            const targetContainer = elUnder?.closest('.section-lessons');

            if (targetLesson && targetLesson !== ds.element) {
                const toSection = parseInt(targetLesson.dataset.section);
                const toLesson = parseInt(targetLesson.dataset.lesson);
                if (!isNaN(toSection) && !isNaN(toLesson) && !isNaN(ds.sourceSection) && !isNaN(ds.sourceLesson)) {
                    this._reorderLessons(ds.sourceSection, ds.sourceLesson, toSection, toLesson);
                    reordered = true;
                }
            } else if (targetContainer) {
                const toSection = parseInt(targetContainer.dataset.section);
                if (!isNaN(toSection) && toSection !== ds.sourceSection && !isNaN(ds.sourceSection) && !isNaN(ds.sourceLesson)) {
                    const targetLessons = this.courseData.sections[toSection]?.lessons;
                    this._reorderLessons(ds.sourceSection, ds.sourceLesson, toSection, targetLessons ? targetLessons.length : 0);
                    reordered = true;
                }
            }
        } else if (ds.type === 'prerequisites') {
            const target = elUnder?.closest('.prereq-item');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.index);
                const arr = this.courseData.prerequisites;
                if (!isNaN(ds.sourceIndex) && !isNaN(toIndex) && ds.sourceIndex >= 0 && ds.sourceIndex < arr.length && toIndex >= 0 && toIndex < arr.length) {
                    const [moved] = arr.splice(ds.sourceIndex, 1);
                    arr.splice(toIndex, 0, moved);
                    reordered = true;
                    this.showToast('Prerequisite reordered successfully ✓');
                }
            }
        } else if (ds.type === 'targetAudience') {
            const target = elUnder?.closest('.audience-item');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.index);
                const arr = this.courseData.targetAudience;
                if (!isNaN(ds.sourceIndex) && !isNaN(toIndex) && ds.sourceIndex >= 0 && ds.sourceIndex < arr.length && toIndex >= 0 && toIndex < arr.length) {
                    const [moved] = arr.splice(ds.sourceIndex, 1);
                    arr.splice(toIndex, 0, moved);
                    reordered = true;
                    this.showToast('Audience reordered successfully ✓');
                }
            }
        }

        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        this.dragState = {
            active: false,
            type: null,
            sourceSection: null,
            sourceLesson: null,
            sourceIndex: null,
            element: null,
            clone: null,
            startX: 0,
            startY: 0,
            offsetX: 0,
            offsetY: 0
        };

        if (reordered) {
            if (ds.type === 'prerequisites') {
                this.renderStep(4, true);
            } else if (ds.type === 'targetAudience') {
                this.renderStep(5, true);
            } else {
                this.renderStep(2, true);
            }
        }
    }

    _onTouchMove(e) {
        if (!this.dragState.active) return;
        e.preventDefault();
        const touch = e.touches[0];
        const fakeEvent = {
            clientX: touch.clientX,
            clientY: touch.clientY,
            startX: this.dragState.startX,
            startY: this.dragState.startY
        };
        this._onMouseMove(fakeEvent);
    }

    _onTouchEnd(e) {
        if (!this.dragState.active) return;
        const touch = e.changedTouches[0];
        const fakeEvent = {
            clientX: touch.clientX,
            clientY: touch.clientY
        };
        this._onMouseUp(fakeEvent);
    }

    _reorderSections(from, to) {
        if (from === to) return;
        const sections = this.courseData.sections;
        if (from < 0 || from >= sections.length || to < 0 || to >= sections.length) return;
        const [moved] = sections.splice(from, 1);
        const adjustedTo = from < to ? to - 1 : to;
        sections.splice(adjustedTo, 0, moved);
        this.showToast('Section moved successfully ✓');
    }

    _reorderLessons(fromS, fromL, toS, toL) {
        if (!this.courseData.sections[fromS] || !this.courseData.sections[toS]) return;
        const src = this.courseData.sections[fromS].lessons;
        const dst = this.courseData.sections[toS].lessons;
        if (!src[fromL]) return;
        const [moved] = src.splice(fromL, 1);
        if (fromS === toS) {
            let adj = toL;
            if (fromL < toL) adj = toL - 1;
            adj = Math.max(0, Math.min(adj, src.length));
            src.splice(adj, 0, moved);
        } else {
            const ins = Math.max(0, Math.min(toL, dst.length));
            dst.splice(ins, 0, moved);
        }
        this.showToast('Lesson moved successfully ✓');
    }

    addSection() {
        this.collectStepData();
        this.courseData.sections.push({
            title: 'New Section',
            description: '',
            duration: '',
            lessons: []
        });
        this.renderStep(2, true);
        this.showToast('Section added');
    }

    removeSection(i) {
        this.collectStepData();
        if (this.courseData.sections.length <= 1) {
            this.showToast('You must have at least one section');
            return;
        }
        this.courseData.sections.splice(i, 1);
        this.renderStep(2, true);
        this.showToast('Section removed');
    }

    duplicateSection(i) {
        this.collectStepData();
        const orig = this.courseData.sections[i];
        const dup = JSON.parse(JSON.stringify(orig));
        dup.title += ' (Copy)';
        dup.lessons.forEach(l => {
            l.content.attachment_files = [];
        });
        this.courseData.sections.splice(i + 1, 0, dup);
        this.renderStep(2, true);
        this.showToast('Section duplicated');
    }

    addLesson(si) {
        this.collectStepData();
        this.courseData.sections[si].lessons.push({
            title: 'New Lesson',
            description: '',
            duration: '',
            type: 'video',
            preview: false,
            published: false,
            completion_criteria: {
                criteria_type: 'watch_video',
                video_watch_percentage: 90,
                quiz_passing_score: null
            },
            content: {
                videoSource: 'file',
                videoUrl: '',
                videoFile: null,
                videoFileName: '',
                textContent: '',
                transcript: '',
                captions: [],
                duration: '',
                attachments: [],
                attachment_files: []
            }
        });
        this.renderStep(2, true);
        this.showToast('Lesson added');
    }

    removeLesson(si, li) {
        this.collectStepData();
        this.courseData.sections[si].lessons.splice(li, 1);
        this.renderStep(2, true);
        this.showToast('Lesson removed');
    }

    duplicateLesson(si, li) {
        this.collectStepData();
        const orig = this.courseData.sections[si].lessons[li];
        const dup = JSON.parse(JSON.stringify(orig));
        dup.title += ' (Copy)';
        dup.content.attachment_files = [];
        this.courseData.sections[si].lessons.splice(li + 1, 0, dup);
        this.renderStep(2, true);
        this.showToast('Lesson duplicated');
    }

    toggleSectionCollapse(si) {
        const lessonsEl = document.getElementById(`sectionLessons${si}`);
        const iconEl = document.getElementById(`collapseIcon${si}`);
        if (lessonsEl) lessonsEl.classList.toggle('collapsed');
        if (iconEl) iconEl.classList.toggle('rotated');
    }

    addTag() {
        const i = document.getElementById('tagInput');
        const v = i?.value?.trim();
        if (!v) return;
        if ((this.courseData.tags || []).includes(v)) {
            this.showToast('Already added');
            return;
        }
        this.courseData.tags = [...(this.courseData.tags || []), v];
        if (i) i.value = '';
        this.renderStep(1);
    }

    removeTag(i) {
        this.courseData.tags.splice(i, 1);
        this.renderStep(1);
    }

    addOutcome() {
        const i = document.getElementById('newOutcome');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.outcomes.push(v);
        if (i) i.value = '';
        this.renderStep(3);
        this.showToast('Outcome added');
    }

    removeOutcome(i) {
        this.courseData.outcomes.splice(i, 1);
        this.renderStep(3);
        this.showToast('Outcome removed');
    }

    addPrerequisite() {
        const i = document.getElementById('newPrereq');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.prerequisites.push(v);
        if (i) i.value = '';
        this.renderStep(4);
        this.showToast('Prerequisite added');
    }

    removePrerequisite(i) {
        this.courseData.prerequisites.splice(i, 1);
        this.renderStep(4);
        this.showToast('Prerequisite removed');
    }

    addAudience() {
        const i = document.getElementById('newAudience');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.targetAudience.push(v);
        if (i) i.value = '';
        this.renderStep(5);
        this.showToast('Audience added');
    }

    removeAudience(i) {
        this.courseData.targetAudience.splice(i, 1);
        this.renderStep(5);
        this.showToast('Audience removed');
    }

    handleThumbnail(file) {
        if (!file) return;
        this.courseData.thumbnail = file;
        this.courseData.thumbnailPreview = URL.createObjectURL(file);
        this.renderStep(7);
        this.showToast('Thumbnail uploaded');
    }

    collectStepData() {
        this.courseData.title = document.getElementById('courseTitle')?.value || this.courseData.title || '';
        this.courseData.subtitle = document.getElementById('courseSubtitle')?.value || this.courseData.subtitle || '';
        this.courseData.shortDescription = document.getElementById('shortDesc')?.value || this.courseData.shortDescription || '';
        this.courseData.category = document.getElementById('courseCategory')?.value || this.courseData.category || '';
        this.courseData.subcategory = document.getElementById('courseSubcategory')?.value || this.courseData.subcategory || '';
        this.courseData.level = document.getElementById('courseLevel')?.value || this.courseData.level || 'intermediate';
        this.courseData.language = document.getElementById('courseLanguage')?.value || this.courseData.language || 'en';
        this.courseData.duration = document.getElementById('courseDuration')?.value || this.courseData.duration || '';
        this.courseData.visibility = document.getElementById('courseVisibility')?.value || this.courseData.visibility || 'public';
        this.courseData.fullDescription = document.getElementById('fullDescription')?.value || this.courseData.fullDescription || '';

        document.querySelectorAll('.section-title-input').forEach(i => {
            const si = parseInt(i.dataset.section);
            if (!isNaN(si) && this.courseData.sections[si]) {
                this.courseData.sections[si].title = i.value || this.courseData.sections[si].title || '';
            }
        });

        document.querySelectorAll('.section-meta-input.description-textarea').forEach(textarea => {
            const si = parseInt(textarea.dataset.section);
            if (!isNaN(si) && this.courseData.sections[si]) {
                this.courseData.sections[si].description = textarea.value || this.courseData.sections[si].description || '';
            }
        });
        document.querySelectorAll('.section-meta-input.duration').forEach(i => {
            const si = parseInt(i.dataset.section);
            if (!isNaN(si) && this.courseData.sections[si]) {
                this.courseData.sections[si].duration = i.value || this.courseData.sections[si].duration || '';
            }
        });

        const priceEl = document.getElementById('coursePrice');
        if (priceEl) {
            const activeOption = document.querySelector('.pricing-option.active');
            this.courseData.priceType = activeOption?.dataset?.type || this.courseData.priceType || 'paid';
            this.courseData.price = parseFloat(priceEl.value) || this.courseData.price || 0;
            this.courseData.discountPrice = document.getElementById('discountPrice')?.value || this.courseData.discountPrice || '';
        }

        const seoTitleEl = document.getElementById('seoTitle');
        if (seoTitleEl) {
            this.courseData.courseTrailer = document.getElementById('courseTrailer')?.value || this.courseData.courseTrailer || '';
            this.courseData.promoVideo = document.getElementById('promoVideo')?.value || this.courseData.promoVideo || '';
            this.courseData.seoTitle = seoTitleEl.value || this.courseData.seoTitle || '';
            this.courseData.seoDescription = document.getElementById('seoDescription')?.value || this.courseData.seoDescription || '';
        }

        this.courseData.version = document.getElementById('courseVersion')?.value?.trim() || this.courseData.version || '1.0';
        this.courseData.versionNotes = document.getElementById('versionNotes')?.value?.trim() || this.courseData.versionNotes || '';
    }

    async submitForReview(){
        const status = "submitted"
        const message = 'Course submitted for review'
        this.createCourse("submitted")
    }

    async createCourse(status, message) {
        this.collectStepData();
        this.courseData.status = 'under_review';
        this.courseData.reviewStatus = 'pending';
        const courseData = mapData(this.courseData);
        const newformData = buildFormData(courseData);
        let courseCreationType = "save-draft"


        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/courses/create/${status}/`,
                {
                    method: 'POST',
                    body: newformData
                }
            );
            const data = await response.json();
            if (!response.ok) {
                throw new Error("Failed to create Course.");
            }

            this.showToast(message);
            setTimeout(() => {
                window.location.href = baseUrl + "/instructor/courses/";
            }, 1000);

        } catch (err) {
            console.log(err);
            this.showToast('Failed to create Courses.');
        }
    }

    nextStep() {
        this.collectStepData();
        if (this.currentStep < this.totalSteps) this.goToStep(this.currentStep + 1);
    }

    prevStep() {
        this.collectStepData();
        if (this.currentStep > 1) this.goToStep(this.currentStep - 1);
    }

    goToStep(s) {
        this.collectStepData();
        this.currentStep = s;
        this.renderStep(s);
    }

    updateProgressUI() {
        document.querySelectorAll('.progress-step').forEach(s => {
            const n = parseInt(s.dataset.step);
            s.classList.remove('active', 'completed');
            if (n === this.currentStep) s.classList.add('active');
            else if (n < this.currentStep) s.classList.add('completed');
        });
        document.querySelectorAll('.step-connector').forEach((c, i) => {
            c.classList.toggle('completed', i + 1 < this.currentStep);
        });
        const prevBtn = document.getElementById('prevStepBtn');
        if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'flex' : 'none';
    }

    updateNavigationButtons() {
        const b = document.getElementById('nextStepBtn');
        const stepLabels = ['', '', 'Curriculum', 'Outcomes', 'Prerequisites', 'Target Audience', 'Pricing', 'Media & SEO', 'Publish'];
        if (this.currentStep < this.totalSteps) {
            if (b) {
                b.innerHTML = `Next: ${stepLabels[this.currentStep + 1]} <i class="fas fa-arrow-right"></i>`;
                b.style.display = 'flex';
            }
        } else {
            if (b) b.style.display = 'none';
        }
    }



    async saveDraft(show) {
        const status = "drafted"
        const message = "Course created and saved as a draft."
        this.CreateCourse(status, message)
        // if (show) this.showToast('Draft saved successfully');
    }



    renderAll() {
        this.renderStep(this.currentStep);
    }

    esc(s) {
        if (!s) return '';
        return s.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    hideLoader() {
        const loader = document.getElementById('loadingOverlay');
        if (loader) loader.classList.add('hidden');
    }

    showToast(m) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = m;
        container.appendChild(t);
        requestAnimationFrame(() => {
            t.style.opacity = '1';
            t.style.transform = 'translateY(0)';
        });
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateY(20px)';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }
    getCurrentDateTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
}

// Initialize on DOM ready
let createCoursePage;
document.addEventListener('DOMContentLoaded', () => {
    createCoursePage = new CreateCoursePage();
});
