// ============================================
// INSTRUCTOR COURSE PREVIEW CONTROLLER
// ============================================

const baseUrl = window.location.origin;
const auth = new Auth({
    "baseURL": window.location.origin + '/api/v1/account/auth',
    "onLogout": ()=>{window.location.href = baseUrl + '/account/auth/login'}
});

class InstructorCoursePreview {
    constructor() {
        this.courseId = this.getCourseIdFromUrl();
        this.currentLessonId = null;
        this.currentLessonType = null;
        this.currentSectionIndex = 0;
        this.currentLessonIndex = 0;
        this.sidebarOpen = true;
        this.courseData = null;
        this.activeTab = 'overview';
        this.lessonContentCache = new Map();
        this.isInitialLoad = true;
        this.videoPlayer = null;
        this.fileModal = null;
        this.fileModalContent = null;

        this.init();
    }

    getCourseIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/instructor\/courses\/([^/]+)\/preview/);
        if (match) return match[1];

        const params = new URLSearchParams(window.location.search);
        return params.get('course_id') || 'course-demo-001';
    }

    getLessonIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/instructor\/courses\/[^/]+\/preview\/(\d+)/);
        return match ? parseInt(match[2]) : null;
    }

    async init() {
        this.bindEvents();
        this.initializeVideoPlayer();
        this.createFileViewerModal();
        await this.loadCourseStructure();
        this.renderSidebar();
        await this.determineStartingLesson();
        this.handleResponsiveSidebar();

        window.addEventListener('resize', () => this.handleResponsiveSidebar());
        window.addEventListener('popstate', (event) => this.handleBrowserNavigation(event));

        this.isInitialLoad = false;
    }

    handleBrowserNavigation(event) {
        if (event.state) {
            if (event.state.lessonId && event.state.lessonId !== this.currentLessonId) {
                this.navigateToLessonById(event.state.lessonId, false, true);
            }
        } else {
            const lessonIdFromUrl = this.getLessonIdFromUrl();
            if (lessonIdFromUrl && lessonIdFromUrl !== this.currentLessonId) {
                this.navigateToLessonById(lessonIdFromUrl, false, true);
            }
        }
    }

    updateBrowserUrl(lessonId = null) {
        let url = `/instructor/courses/${this.courseId}/preview/`;
        if (lessonId) url += `${lessonId}`;

        const state = {
            courseId: this.courseId,
            lessonId: lessonId || this.currentLessonId
        };

        window.history.pushState(state, '', url);
    }

    bindEvents() {
        const sidebarToggle = document.getElementById('sidebarToggleBtn');
        if (sidebarToggle) sidebarToggle.addEventListener('click', () => this.toggleSidebar());

        const sidebarCollapse = document.getElementById('sidebarCollapseBtn');
        if (sidebarCollapse) sidebarCollapse.addEventListener('click', () => this.toggleSidebar(false));

        const mobileCurriculum = document.getElementById('mobileCurriculumBtn');
        if (mobileCurriculum) mobileCurriculum.addEventListener('click', () => this.toggleSidebar());

        const navPrev = document.getElementById('navPrevLesson');
        if (navPrev) navPrev.addEventListener('click', () => this.navigateLesson(-1));

        const navNext = document.getElementById('navNextLesson');
        if (navNext) navNext.addEventListener('click', () => this.navigateLesson(1));

        const mobilePrev = document.getElementById('mobilePrevBtn');
        if (mobilePrev) mobilePrev.addEventListener('click', () => this.navigateLesson(-1));

        const mobileNext = document.getElementById('mobileNextBtn');
        if (mobileNext) mobileNext.addEventListener('click', () => this.navigateLesson(1));

        const closePreview = document.getElementById('closePreviewBtn');
        if (closePreview) closePreview.addEventListener('click', () => this.closePreview());

        const videoPlay = document.getElementById('videoBigPlayBtn');
        if (videoPlay) videoPlay.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleVideoPlay();
        });

        const videoContainer = document.getElementById('videoContainer');
        if (videoContainer) {
            videoContainer.addEventListener('click', (e) => {
                if (!e.target.closest('button') && !e.target.closest('video')) {
                    this.toggleVideoPlay();
                }
            });
        }

        const lessonTabs = document.querySelectorAll('.lesson-tab');
        lessonTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
    }

    initializeVideoPlayer() {
        const videoContainer = document.getElementById('videoContainer');
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        if (!videoContainer) return;

        let videoElement = document.getElementById('mainVideoPlayer');

        if (!videoElement) {
            if (videoPlaceholder) videoPlaceholder.style.display = 'none';

            videoElement = document.createElement('video');
            videoElement.id = 'mainVideoPlayer';
            videoElement.className = 'main-video-player';
            videoElement.controls = false;
            videoElement.preload = 'auto';
            videoElement.style.cssText = 'width:100%;height:100%;object-fit:contain;background:#000;border-radius:8px;cursor:pointer;display:block;';
            videoElement.setAttribute('playsinline', '');
            videoElement.setAttribute('webkit-playsinline', '');

            const videoOverlay = document.getElementById('videoOverlay');
            if (videoOverlay) {
                videoContainer.insertBefore(videoElement, videoOverlay);
            } else {
                videoContainer.appendChild(videoElement);
            }
        }

        this.videoPlayer = videoElement;

        videoElement.addEventListener('play', () => this.onVideoPlay());
        videoElement.addEventListener('pause', () => this.onVideoPause());
        videoElement.addEventListener('ended', () => this.onVideoEnded());
        videoElement.addEventListener('error', (e) => this.onVideoError(e));
    }

    createFileViewerModal() {
        const existingModal = document.getElementById('fileViewerModal');
        if (existingModal) {
            this.fileModal = existingModal;
            this.fileModalContent = document.getElementById('fileViewerContent');
        } else {
            const modal = document.createElement('div');
            modal.id = 'fileViewerModal';
            modal.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:10000;overflow:auto;';

            modal.innerHTML = `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 20px;background:#1F2937;border-bottom:1px solid #2A2A3E;">
                    <h3 id="fileViewerTitle" style="color:#FFF;margin:0;font-size:1rem;"></h3>
                    <div style="display:flex;gap:12px;align-items:center;">
                        <a id="fileViewerDownloadBtn" href="#" download style="color:#8B5CF6;text-decoration:none;font-size:0.9rem;display:flex;align-items:center;gap:6px;">
                            <i class="fas fa-download"></i> Download
                        </a>
                        <button id="fileViewerCloseBtn" style="background:rgba(255,255,255,0.1);border:none;color:#FFF;width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:1.2rem;display:flex;align-items:center;justify-content:center;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div id="fileViewerContent" style="display:flex;align-items:center;justify-content:center;min-height:calc(100% - 57px);padding:20px;"></div>
            `;

            document.body.appendChild(modal);
            this.fileModal = modal;
            this.fileModalContent = modal.querySelector('#fileViewerContent');
        }

        document.getElementById('fileViewerCloseBtn').addEventListener('click', () => this.closeFileViewer());

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.fileModal.style.display === 'block') {
                this.closeFileViewer();
            }
        });

        this.fileModal.addEventListener('click', (e) => {
            if (e.target === this.fileModal) this.closeFileViewer();
        });
    }

    async loadCourseStructure() {
        const data = await this.fetchCourseStructure();
        this.courseData = data;

        const navTitle = document.getElementById('navCourseTitle');
        if (navTitle && data.courseTitle) navTitle.textContent = data.courseTitle;

        this.updateCourseInfo();
    }

    async fetchCourseStructure() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/course/${this.courseId}/preview/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch course curriculum');
            const data = await response.json();

            return this.processCourseStructure(data);
        } catch (error) {
            console.warn('Using dummy curriculum data:', error.message);
            return this.getDummyCurriculum(this.courseId);
        }
    }

    processCourseStructure(apiData) {
        if (!apiData || !apiData.sections) return apiData;

        if (apiData.sections && Array.isArray(apiData.sections)) {
            apiData.sections = apiData.sections.map(section => ({
                ...section,
                lessons: (section.lessons || []).map(lesson => this.normalizeLessonData(lesson))
            }));
        }

        return apiData;
    }

    normalizeLessonData(lesson) {
        return {
            id: lesson.id,
            title: lesson.title,
            type: lesson.type,
            duration: lesson.duration || this.getDurationString(lesson.duration_seconds),
            durationSeconds: lesson.duration_seconds || 0,
            order: lesson.order,
            isPublished: lesson.is_published || lesson.isPublished || false,
            hasResources: lesson.has_resources || false,
            file_url: lesson.file_url || null,
            file_name: lesson.file_name || null,
            quizData: lesson.quizData || null,
            assignmentData: lesson.assignmentData || null,
            _raw: lesson
        };
    }

    getDurationString(durationSeconds) {
        if (!durationSeconds) return 'N/A';
        const hours = Math.floor(durationSeconds / 3600);
        const minutes = Math.floor((durationSeconds % 3600) / 60);
        if (hours > 0) return `${hours} hr ${minutes} min`;
        return `${minutes} min`;
    }

    updateCourseInfo() {
        if (!this.courseData) return;

        const sections = this.courseData.sections || [];
        const allLessons = this.getAllLessons();
        const totalDuration = allLessons.reduce((sum, lesson) => sum + (lesson.durationSeconds || 0), 0);

        document.getElementById('sidebarSectionCount').textContent = `${sections.length} Sections`;
        document.getElementById('sidebarLessonCount').textContent = `${allLessons.length} Lessons`;
        document.getElementById('sidebarTotalDuration').textContent = this.formatTotalDuration(totalDuration);
    }

    formatTotalDuration(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    }

    async loadLessonContent(lessonId) {
        if (this.lessonContentCache.has(lessonId)) {
            return this.lessonContentCache.get(lessonId);
        }

        this.showContentLoading();
        const content = await this.fetchLessonContent(lessonId);
        this.lessonContentCache.set(lessonId, content);
        return content;
    }

    async fetchLessonContent(lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/course/${this.courseId}/lesson/${lessonId}/preview/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch lesson content');
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Using dummy lesson content:', error.message);
            return this.getDummyLessonContent(lessonId);
        }
    }

    showContentLoading() {
        ['videoPlayerSection', 'articleSection', 'quizSection', 'assignmentSection',
         'fileSection', 'liveSessionSection', 'codingExerciseSection'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        const articleSection = document.getElementById('articleSection');
        if (articleSection) {
            articleSection.style.display = '';
            const body = document.getElementById('articleBody');
            if (body) {
                body.innerHTML = `<div style="text-align:center;padding:60px;"><div style="display:inline-block;width:40px;height:40px;border:3px solid #2A2A3E;border-top-color:#8B5CF6;border-radius:50%;animation:spin 0.8s linear infinite;"></div><p style="color:#888;margin-top:16px;">Loading...</p></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>`;
            }
        }
    }

    async determineStartingLesson() {
        let targetId = this.getLessonIdFromUrl();
        const all = this.getAllLessons();

        if (!all.length) return;

        if (targetId && !all.some(l => l.id === targetId)) {
            targetId = null;
        }

        if (!targetId && all.length) {
            targetId = all[0].id;
        }

        if (targetId) {
            await this.navigateToLessonById(targetId, true);
        }
    }

    renderSidebar() {
        const sc = document.getElementById('sidebarCurriculum');
        if (!sc) return;

        if (!this.courseData?.sections) {
            sc.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">No curriculum available</p>';
            return;
        }

        let html = '';

        this.courseData.sections.forEach((section, si) => {
            html += `
                <div class="curriculum-section">
                    <div class="curriculum-section-header ${si === 0 ? 'open' : ''}" onclick="previewInstance.toggleSection(this)">
                        <div class="section-header-left">
                            <i class="fas fa-chevron-down section-chevron"></i>
                            <span class="section-number">Section ${si + 1}</span>
                        </div>
                        <div class="section-header-right">
                            <span class="section-title-text">${this.escapeHtml(section.title)}</span>
                            <span class="section-progress">${section.lessons.length} lessons</span>
                        </div>
                    </div>
                    <div class="curriculum-lessons" style="display:${si === 0 ? 'block' : 'none'};">
                        ${section.lessons.map(lesson => {
                            const isActive = lesson.id === this.currentLessonId;
                            return `
                                <div class="curriculum-lesson-item ${isActive ? 'active' : ''}"
                                     data-lesson="${lesson.id}"
                                     onclick="previewInstance.navigateToLessonById(${lesson.id})">
                                    <div class="lesson-item-left">
                                        <span class="lesson-status-icon">
                                            ${lesson.isPublished
                                                ? '<span class="lesson-published-badge" title="Published"></span>'
                                                : '<span class="lesson-draft-badge" title="Draft"></span>'}
                                        </span>
                                        <span class="lesson-item-title">${this.escapeHtml(lesson.title)}</span>
                                    </div>
                                    <div class="lesson-item-right">
                                        <span class="lesson-item-type ${lesson.type}">${this.getTypeIcon(lesson.type)}</span>
                                        <span class="lesson-item-duration">${lesson.duration}</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        });

        sc.innerHTML = html;

        if (this.currentLessonId) {
            this.updateSidebarActive();
        }
    }

    toggleSection(header) {
        if (!header) return;
        header.classList.toggle('open');
        const lessons = header.nextElementSibling;
        if (lessons) {
            lessons.style.display = lessons.style.display === 'none' ? '' : 'none';
        }
    }

    async navigateToLessonById(lessonId, isInit = false, isBrowserNav = false) {
        this.stopVideoPlayback();

        let found = false;

        for (let si = 0; si < this.courseData.sections.length; si++) {
            const section = this.courseData.sections[si];
            for (let li = 0; li < section.lessons.length; li++) {
                if (section.lessons[li].id === lessonId) {
                    this.currentSectionIndex = si;
                    this.currentLessonIndex = li;
                    this.currentLessonId = lessonId;
                    found = true;
                    break;
                }
            }
            if (found) break;
        }

        if (found) {
            let lesson = this.getCurrentLesson();

            if (lesson && !this.lessonContentCache.has(lessonId)) {
                const content = await this.loadLessonContent(lessonId);
                Object.assign(lesson, content);
            } else if (lesson && this.lessonContentCache.has(lessonId)) {
                Object.assign(lesson, this.lessonContentCache.get(lessonId));
            }

            this.renderLesson();
            this.updateSidebarActive();
            this.scrollToActiveLesson();

            if (!isInit && !isBrowserNav) {
                this.updateBrowserUrl(lessonId);
            }
        }
    }

    navigateLesson(dir) {
        const all = this.getAllLessons();
        const idx = all.findIndex(l => l.id === this.currentLessonId) + dir;

        if (idx >= 0 && idx < all.length) {
            this.navigateToLessonById(all[idx].id);
        }
    }

    getAllLessons() {
        let all = [];
        (this.courseData?.sections || []).forEach(section => {
            if (section.lessons) {
                all = all.concat(section.lessons);
            }
        });
        return all;
    }

    getCurrentLesson() {
        const section = this.courseData?.sections?.[this.currentSectionIndex];
        return section?.lessons?.[this.currentLessonIndex] || null;
    }

    scrollToActiveLesson() {
        setTimeout(() => {
            const el = document.querySelector('.curriculum-lesson-item.active');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }

    renderLesson() {
        const lesson = this.getCurrentLesson();
        if (!lesson) return;

        this.currentLessonType = lesson.type;

        ['videoPlayerSection', 'articleSection', 'quizSection', 'assignmentSection',
         'fileSection', 'liveSessionSection', 'codingExerciseSection'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        document.getElementById('lessonInfoBar').style.display = 'none';
        document.getElementById('lessonTabs').style.display = 'none';
        document.getElementById('lessonTabContent').style.display = 'none';

        switch (lesson.type) {
            case 'video':
                this.renderVideoLesson(lesson);
                break;
            case 'article':
                this.renderArticleLesson(lesson);
                break;
            case 'quiz':
                this.renderQuizLesson(lesson);
                break;
            case 'assignment':
                this.renderAssignmentLesson(lesson);
                break;
            case 'file':
                this.renderFileLesson(lesson);
                break;
            case 'live_session':
                this.renderLiveSessionLesson(lesson);
                break;
            case 'coding_exercise':
                this.renderCodingExerciseLesson(lesson);
                break;
            default:
                this.renderDefaultLesson(lesson);
        }

        const all = this.getAllLessons();
        const currentIndex = all.findIndex(l => l.id === lesson.id);

        document.getElementById('navLessonIndicator').textContent = `Lesson ${currentIndex + 1} of ${all.length}`;
        document.getElementById('mobileLessonCount').textContent = `${currentIndex + 1} / ${all.length}`;

        const prevBtn = document.getElementById('navPrevLesson');
        const nextBtn = document.getElementById('navNextLesson');
        const mobilePrevBtn = document.getElementById('mobilePrevBtn');
        const mobileNextBtn = document.getElementById('mobileNextBtn');

        if (prevBtn) prevBtn.disabled = currentIndex === 0;
        if (nextBtn) nextBtn.disabled = currentIndex === all.length - 1;
        if (mobilePrevBtn) mobilePrevBtn.disabled = currentIndex === 0;
        if (mobileNextBtn) mobileNextBtn.disabled = currentIndex === all.length - 1;
    }

    renderVideoLesson(lesson) {
        const vs = document.getElementById('videoPlayerSection');
        if (vs) vs.style.display = '';

        const videoPlayer = this.videoPlayer;
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        const videoOverlay = document.getElementById('videoOverlay');
        const videoDescription = document.getElementById('videoDescription');
        const videoDescriptionText = document.getElementById('videoDescriptionText');

        const videoUrl = lesson.videoUrl || lesson.video_url || lesson._raw?.video_url || lesson._raw?.videoUrl;
        const description = lesson.description || lesson.video_description || lesson._raw?.description || '';

        if (videoPlayer && videoUrl) {
            videoPlayer.src = videoUrl;
            videoPlayer.load();
            videoPlayer.style.display = 'block';
            if (videoPlaceholder) videoPlaceholder.style.display = 'none';
            if (videoOverlay) videoOverlay.style.display = 'flex';
        } else {
            if (videoPlayer) videoPlayer.style.display = 'none';
            if (videoPlaceholder) {
                videoPlaceholder.style.display = 'flex';
                const placeholderText = document.getElementById('videoPlaceholderText');
                if (placeholderText) {
                    placeholderText.textContent = lesson.isPublished
                        ? 'No video uploaded yet'
                        : `${lesson.title} (Draft)`;
                }
            }
            if (videoOverlay) videoOverlay.style.display = 'none';
        }

        if (videoDescription && videoDescriptionText && description) {
            videoDescription.style.display = '';
            videoDescriptionText.textContent = description;
        } else if (videoDescription) {
            videoDescription.style.display = 'none';
        }

        this.showLessonInfo(lesson);
        this.showLessonTabs(lesson);
    }

    renderArticleLesson(lesson) {
        const as = document.getElementById('articleSection');
        if (as) as.style.display = '';

        document.getElementById('articleTitle').textContent = lesson.title;
        document.getElementById('articleReadTime').innerHTML =
            `<i class="fas fa-clock"></i> ${lesson.duration} read`;

        const articleContent = lesson.articleContent || lesson.article_content || lesson._raw?.article_content || lesson._raw?.articleContent || '<p>No article content available.</p>';

        const articleBody = document.getElementById('articleBody');
        if (articleBody) {
            articleBody.innerHTML = articleContent;
        }

        this.showLessonInfo(lesson);
        this.showLessonTabs(lesson);
    }

    renderQuizLesson(lesson) {
        const qs = document.getElementById('quizSection');
        if (qs) qs.style.display = '';

        document.getElementById('quizTitle').textContent = lesson.title;

        const quizData = lesson.quizData || lesson._raw?.quizData || lesson._raw?.quiz_data;

        if (quizData && quizData.questions) {
            const questions = quizData.questions;
            document.getElementById('quizQuestionCount').innerHTML =
                `<i class="fas fa-circle-question"></i> ${questions.length} Questions`;
            document.getElementById('quizPassScore').innerHTML =
                `<i class="fas fa-trophy"></i> Pass Score: ${quizData.passScore || quizData.pass_score || 60}%`;

            const previewContent = document.getElementById('quizPreviewContent');
            if (previewContent) {
                previewContent.innerHTML = questions.map((question, index) =>
                    this.renderQuizQuestionPreview(question, index)
                ).join('');
            }
        } else {
            document.getElementById('quizQuestionCount').innerHTML =
                `<i class="fas fa-circle-question"></i> 0 Questions`;
            document.getElementById('quizPassScore').innerHTML =
                `<i class="fas fa-trophy"></i> Pass Score: 0%`;

            const previewContent = document.getElementById('quizPreviewContent');
            if (previewContent) {
                previewContent.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">No quiz questions available.</p>';
            }
        }

        this.showLessonInfo(lesson);
    }

    renderQuizQuestionPreview(question, index) {
        let optionsHTML = '';

        const questionType = question.question_type || question.questionType || 'single_choice';
        const questionText = question.text || question.question || '';
        const choices = question.choices || question.options || [];
        const explanation = question.explanation || '';

        if (questionType === 'short_answer') {
            optionsHTML = `<div class="quiz-short-answer-preview">Short answer input will appear here</div>`;
        } else if (questionType === 'true_false') {
            optionsHTML = `
                <div class="quiz-true-false-preview">
                    <div class="quiz-tf-option true">True</div>
                    <div class="quiz-tf-option false">False</div>
                </div>
            `;
        } else {
            optionsHTML = `
                <div class="quiz-options-preview">
                    ${choices.map((choice, choiceIndex) => `
                        <div class="quiz-option-preview">
                            <span class="quiz-option-letter-preview">${String.fromCharCode(65 + choiceIndex)}</span>
                            <span class="quiz-option-text-preview">${this.escapeHtml(choice.text || choice)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <div class="quiz-question-preview">
                <div class="quiz-question-header">
                    <span class="quiz-question-number">Question ${index + 1}</span>
                    <span class="quiz-question-type">${this.getQuestionTypeLabel(questionType)}</span>
                </div>
                <p class="quiz-question-text">${this.escapeHtml(questionText)}</p>
                ${optionsHTML}
                ${explanation ? `<p style="color:#888;font-size:0.8rem;margin-top:12px;"><strong>Explanation:</strong> ${this.escapeHtml(explanation)}</p>` : ''}
            </div>
        `;
    }

    renderAssignmentLesson(lesson) {
        const asg = document.getElementById('assignmentSection');
        if (asg) asg.style.display = '';

        document.getElementById('assignmentTitle').textContent = lesson.title;

        const assignmentData = lesson.assignmentData || lesson._raw?.assignmentData || lesson._raw?.assignment_data;

        if (assignmentData) {
            const maxScore = assignmentData.maxScore || assignmentData.max_score || 100;
            const dueDate = assignmentData.dueDate || assignmentData.due_date || null;
            const instructions = assignmentData.instructions || 'No instructions provided.';
            const acceptedFileTypes = assignmentData.acceptedFileTypes || assignmentData.accepted_file_types || '';
            const maxFileSizeMB = assignmentData.maxFileSizeMB || assignmentData.max_file_size_mb || 50;

            document.getElementById('assignmentMaxScore').innerHTML =
                `<i class="fas fa-star"></i> Max Score: ${maxScore}`;
            document.getElementById('assignmentDueDate').innerHTML =
                `<i class="fas fa-calendar"></i> Due Date: ${dueDate ? new Date(dueDate).toLocaleDateString() : 'No due date'}`;

            const details = document.getElementById('assignmentDetails');
            if (details) {
                details.innerHTML = `
                    <h3>Assignment Instructions</h3>
                    <p>${this.escapeHtml(instructions)}</p>
                    ${acceptedFileTypes ? `<p><strong>Accepted File Types:</strong> ${this.escapeHtml(acceptedFileTypes)}</p>` : ''}
                    ${maxFileSizeMB ? `<p><strong>Max File Size:</strong> ${maxFileSizeMB} MB</p>` : ''}
                `;
            }
        } else {
            document.getElementById('assignmentMaxScore').innerHTML =
                `<i class="fas fa-star"></i> Max Score: 100`;
            document.getElementById('assignmentDueDate').innerHTML =
                `<i class="fas fa-calendar"></i> Due Date: No due date`;

            const details = document.getElementById('assignmentDetails');
            if (details) {
                details.innerHTML = '<p style="color:#888;">No assignment details available.</p>';
            }
        }

        this.showLessonInfo(lesson);
    }

    renderFileLesson(lesson) {
        const fs = document.getElementById('fileSection');
        if (fs) fs.style.display = '';

        document.getElementById('fileTitle').textContent = lesson.title;

        const filePreview = document.getElementById('filePreview');
        if (filePreview) {

            const fileUrl = lesson.fileUrl || lesson.file_url;
            const fileName = lesson.file_name || lesson.file_name || this.getDisplayFileName(fileUrl, '');

            if (fileUrl) {
                const fileType = this.getFileType(fileUrl, fileName);

                filePreview.innerHTML = `
                    <div class="file-preview-icon">
                        <i class="fas ${this.getFileTypeIcon(fileType)}"></i>
                    </div>
                    <h3 class="file-preview-name">${this.escapeHtml(fileName)}</h3>
                    <p class="file-preview-type">${this.getFileTypeLabel(fileType)}</p>
                    <div class="file-preview-actions">
                        <a href="${this.escapeHtml(fileUrl)}" class="btn-preview-file"
                           onclick="event.preventDefault(); previewInstance.openFileViewer('${this.escapeHtml(fileUrl)}', '${this.escapeHtml(fileName)}')">
                            <i class="fas fa-eye"></i> Preview
                        </a>
                        <a href="${this.escapeHtml(fileUrl)}" download class="btn-download-file">
                            <i class="fas fa-download"></i> Download
                        </a>
                    </div>
                `;
            } else {
                filePreview.innerHTML = `
                    <div class="file-preview-icon">
                        <i class="fas fa-file"></i>
                    </div>
                    <h3 class="file-preview-name">${this.escapeHtml(lesson.title)}</h3>
                    <p class="file-preview-type">No file uploaded</p>
                `;
            }
        }

        this.showLessonInfo(lesson);
        this.showLessonTabs(lesson);
    }

    renderLiveSessionLesson(lesson) {
        const lss = document.getElementById('liveSessionSection');
        if (lss) lss.style.display = '';

        document.getElementById('liveSessionTitle').textContent = lesson.title;

        this.showLessonInfo(lesson);
    }

    renderCodingExerciseLesson(lesson) {
        const ces = document.getElementById('codingExerciseSection');
        if (ces) ces.style.display = '';

        document.getElementById('codingExerciseTitle').textContent = lesson.title;

        this.showLessonInfo(lesson);
    }

    renderDefaultLesson(lesson) {
        const as = document.getElementById('articleSection');
        if (as) as.style.display = '';

        document.getElementById('articleTitle').textContent = lesson.title;

        const articleBody = document.getElementById('articleBody');
        if (articleBody) {
            articleBody.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">Content type not supported.</p>';
        }

        this.showLessonInfo(lesson);
    }

    showLessonInfo(lesson) {
        document.getElementById('lessonInfoBar').style.display = 'flex';
        document.getElementById('currentLessonTitle').textContent = lesson.title;

        const typeBadge = document.getElementById('lessonTypeBadge');
        if (typeBadge) {
            typeBadge.innerHTML = `${this.getTypeIcon(lesson.type)} ${this.getTypeLabel(lesson.type)}`;
            typeBadge.className = `lesson-type-badge ${lesson.type}`;
        }

        const durationBadge = document.getElementById('lessonDurationBadge');
        if (durationBadge) {
            durationBadge.innerHTML = `<i class="fas fa-clock"></i> ${lesson.duration}`;
        }
    }

    showLessonTabs(lesson) {
        document.getElementById('lessonTabs').style.display = 'flex';
        document.getElementById('lessonTabContent').style.display = 'block';

        document.querySelectorAll('.lesson-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

        const overviewTab = document.querySelector('.lesson-tab[data-tab="overview"]');
        const overviewPanel = document.getElementById('tabOverview');

        if (overviewTab) overviewTab.classList.add('active');
        if (overviewPanel) overviewPanel.classList.add('active');

        this.activeTab = 'overview';

        this.renderOverviewContent(lesson);
        this.renderResources(lesson.resources || lesson._raw?.resources || []);
        this.renderTranscript(lesson.transcript || lesson._raw?.transcript || []);

        const resourceCount = document.getElementById('resourceCount');
        if (resourceCount) {
            const resources = lesson.resources || lesson._raw?.resources || [];
            resourceCount.textContent = resources.length;
        }
    }

    renderOverviewContent(lesson) {
        const overviewContent = document.getElementById('overviewContent');
        if (!overviewContent) return;

        const overview = lesson.overview || lesson._raw?.overview || '';
        const description = lesson.description || lesson.video_description || lesson._raw?.description || '';
        const articleContent = lesson.articleContent || lesson.article_content || lesson._raw?.article_content || '';

        if (overview) {
            overviewContent.innerHTML = overview;
        } else if (description) {
            overviewContent.innerHTML = `<p>${this.escapeHtml(description)}</p>`;
        } else if (articleContent) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = articleContent;
            const firstParagraph = tempDiv.querySelector('p');
            overviewContent.innerHTML = firstParagraph
                ? `<p>${firstParagraph.textContent}</p>`
                : '<p>No overview available.</p>';
        } else {
            overviewContent.innerHTML = '<p>No overview available for this lesson.</p>';
        }
    }

    renderResources(resources) {
        const resourcesArea = document.getElementById('resourcesArea');
        if (!resourcesArea) return;

        const normalizedResources = this.normalizeResources(resources);

        if (!normalizedResources.length) {
            resourcesArea.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-paperclip"></i>
                    <p>No resources available for this lesson.</p>
                </div>
            `;
            return;
        }

        resourcesArea.innerHTML = normalizedResources.map(resource => `
            <div class="resource-item-card">
                <div class="resource-icon">
                    <i class="fas ${this.getResourceIconClass(resource.type || 'file')}"></i>
                </div>
                <div class="resource-info">
                    <span class="resource-name">${this.escapeHtml(resource.name)}</span>
                    <span class="resource-size">${this.escapeHtml(resource.size || 'Unknown size')}</span>
                </div>
                <a href="${this.escapeHtml(resource.url || '#')}"
                   download="${this.escapeHtml(resource.name)}"
                   class="resource-download-btn">
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        `).join('');
    }

    renderTranscript(transcript) {
        const transcriptArea = document.getElementById('transcriptArea');
        if (!transcriptArea) return;

        if (!transcript || !transcript.length) {
            transcriptArea.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No transcript available for this lesson.</p>
                </div>
            `;
            return;
        }

        transcriptArea.innerHTML = transcript.map(line => `
            <div class="transcript-line">
                <span class="transcript-time">${this.escapeHtml(line.time || line.timestamp || '00:00')}</span>
                <p>${this.escapeHtml(line.text || '')}</p>
            </div>
        `).join('');
    }

    switchTab(tab) {
        this.activeTab = tab;

        document.querySelectorAll('.lesson-tab').forEach(t => t.classList.remove('active'));
        const activeTab = document.querySelector(`.lesson-tab[data-tab="${tab}"]`);
        if (activeTab) activeTab.classList.add('active');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const activePanel = document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
        if (activePanel) activePanel.classList.add('active');
    }

    updateSidebarActive() {
        document.querySelectorAll('.curriculum-lesson-item').forEach(el => {
            el.classList.remove('active');
            if (parseInt(el.dataset.lesson) === this.currentLessonId) {
                el.classList.add('active');

                const lessonsContainer = el.closest('.curriculum-lessons');
                if (lessonsContainer && lessonsContainer.style.display === 'none') {
                    lessonsContainer.style.display = '';
                    const header = lessonsContainer.previousElementSibling;
                    if (header) header.classList.add('open');
                }
            }
        });
    }

    toggleVideoPlay() {
        if (!this.videoPlayer) return;

        if (this.videoPlayer.paused || this.videoPlayer.ended) {
            this.videoPlayer.play().catch(err => {
                console.error('Video play failed:', err);
                this.showToast('Unable to play video. Check the source URL.');
            });
        } else {
            this.videoPlayer.pause();
        }
    }

    onVideoPlay() {
        const overlay = document.getElementById('videoOverlay');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');

        if (overlay) {
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
        }
        if (bigPlayBtn) {
            bigPlayBtn.style.opacity = '0';
            bigPlayBtn.style.pointerEvents = 'none';
        }
    }

    onVideoPause() {
        const overlay = document.getElementById('videoOverlay');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');

        if (overlay) {
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
        }
        if (bigPlayBtn) {
            bigPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
            bigPlayBtn.style.opacity = '1';
            bigPlayBtn.style.pointerEvents = 'auto';
        }
    }

    onVideoEnded() {
        const overlay = document.getElementById('videoOverlay');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');

        if (overlay) {
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
        }
        if (bigPlayBtn) {
            bigPlayBtn.innerHTML = '<i class="fas fa-redo"></i>';
            bigPlayBtn.style.opacity = '1';
            bigPlayBtn.style.pointerEvents = 'auto';
        }
    }

    onVideoError(e) {
        console.error('Video error:', e);
        this.showToast('Error loading video. Please try again.');
    }

    stopVideoPlayback() {
        if (this.videoPlayer) {
            this.videoPlayer.pause();
            this.videoPlayer.src = '';
            this.videoPlayer.style.display = 'none';
        }

        const videoPlaceholder = document.getElementById('videoPlaceholder');
        const videoOverlay = document.getElementById('videoOverlay');

        if (videoPlaceholder) videoPlaceholder.style.display = 'flex';
        if (videoOverlay) videoOverlay.style.display = 'flex';
    }

    async openFileViewer(fileUrl, fileName) {
        if (!this.fileModal || !this.fileModalContent) return;

        const displayName = this.getDisplayFileName(fileUrl, fileName);
        const fileType = this.getFileType(fileUrl, fileName);
        const extension = this.getFileExtension(fileUrl, fileName);

        document.getElementById('fileViewerTitle').textContent = displayName;
        const downloadBtn = document.getElementById('fileViewerDownloadBtn');
        if (downloadBtn) downloadBtn.href = fileUrl;

        let contentHTML = '';

        switch (fileType) {
            case 'image':
                contentHTML = `<img src="${this.escapeHtml(fileUrl)}" alt="${this.escapeHtml(displayName)}" style="max-width:100%;max-height:80vh;object-fit:contain;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.5);" onerror="this.parentElement.innerHTML='<div style=\\'text-align:center;color:#EF4444;\\'><i class=\\'fas fa-exclamation-triangle\\' style=\\'font-size:3rem;\\'></i><p>Failed to load image</p></div>'">`;
                break;

            case 'pdf':
                contentHTML = `<iframe src="${this.escapeHtml(fileUrl)}" style="width:100%;height:80vh;border:none;border-radius:8px;background:#FFF;" onerror="this.parentElement.innerHTML='<div style=\\'text-align:center;color:#EF4444;\\'><i class=\\'fas fa-exclamation-triangle\\' style=\\'font-size:3rem;\\'></i><p>Failed to load PDF</p></div>'"></iframe>`;
                break;

            case 'text':
            case 'code':
                contentHTML = '<div style="width:100%;max-width:900px;background:#111827;border-radius:8px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.5);"><div style="display:flex;align-items:center;justify-content:space-between;padding:8px 16px;background:#1F2937;border-bottom:1px solid #2A2A3E;"><span style="color:#888;font-size:0.8rem;">' + (fileType === 'code' ? 'Code Viewer' : 'Text Viewer') + '</span><span style="color:#8B5CF6;font-size:0.8rem;">' + (extension ? '.' + extension : '') + '</span></div><pre id="textFileContent" style="margin:0;padding:16px;color:#E5E7EB;font-size:0.9rem;line-height:1.6;overflow:auto;max-height:70vh;white-space:pre-wrap;word-wrap:break-word;background:#111827;"></pre></div>';
                setTimeout(async () => {
                    try {
                        const response = await fetch(fileUrl);
                        const text = await response.text();
                        const preEl = document.getElementById('textFileContent');
                        if (preEl) preEl.textContent = text;
                    } catch (e) {
                        const preEl = document.getElementById('textFileContent');
                        if (preEl) preEl.innerHTML = '<span style="color:#EF4444;">Failed to load file content</span>';
                    }
                }, 100);
                break;

            case 'video':
                contentHTML = `<video controls style="max-width:100%;max-height:80vh;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.5);" onerror="this.parentElement.innerHTML='<div style=\\'text-align:center;color:#EF4444;\\'><i class=\\'fas fa-exclamation-triangle\\' style=\\'font-size:3rem;\\'></i><p>Failed to load video</p></div>'"><source src="${this.escapeHtml(fileUrl)}">Your browser does not support the video tag.</video>`;
                break;

            case 'audio':
                contentHTML = `<div style="text-align:center;max-width:600px;width:100%;"><div style="font-size:4rem;color:#8B5CF6;margin-bottom:20px;"><i class="fas fa-file-audio"></i></div><h4 style="color:#FFF;margin-bottom:16px;">${this.escapeHtml(displayName)}</h4><audio controls style="width:100%;" onerror="this.parentElement.innerHTML='<div style=\\'text-align:center;color:#EF4444;\\'><i class=\\'fas fa-exclamation-triangle\\' style=\\'font-size:3rem;\\'></i><p>Failed to load audio</p></div>'"><source src="${this.escapeHtml(fileUrl)}">Your browser does not support the audio tag.</audio></div>`;
                break;

            default:
                contentHTML = `<div style="text-align:center;max-width:500px;"><div style="font-size:5rem;color:#6B7280;margin-bottom:20px;"><i class="fas fa-file"></i></div><h3 style="color:#FFF;margin-bottom:8px;">${this.escapeHtml(displayName)}</h3><p style="color:#888;margin-bottom:8px;">File type: ${extension ? '.' + extension.toUpperCase() : 'Unknown'}</p><p style="color:#666;font-size:0.9rem;">This file type cannot be previewed directly. Please download to view.</p><a href="${this.escapeHtml(fileUrl)}" download style="display:inline-block;margin-top:16px;padding:12px 24px;background:rgba(139,92,246,0.15);color:#8B5CF6;border:1px solid rgba(139,92,246,0.3);border-radius:8px;text-decoration:none;font-weight:600;"><i class="fas fa-download"></i> Download File</a></div>`;
        }

        this.fileModalContent.innerHTML = contentHTML;
        this.fileModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeFileViewer() {
        if (this.fileModal) {
            this.fileModal.style.display = 'none';
            if (this.fileModalContent) this.fileModalContent.innerHTML = '';
            document.body.style.overflow = '';
        }
    }

    closePreview() {
        window.location.href = baseUrl + `/instructor/courses/${this.courseId}/`;
    }

    toggleSidebar(force) {
        this.sidebarOpen = typeof force === 'boolean' ? force : !this.sidebarOpen;
        const sidebar = document.getElementById('previewSidebar');
        if (sidebar) {
            sidebar.classList.toggle('open', this.sidebarOpen);
        }
    }

    handleResponsiveSidebar() {
        this.toggleSidebar(window.innerWidth > 1024);
    }

    // ============================================
    // UTILITY METHODS
    // ============================================

    getExtensionFromUrl(url) {
        if (!url) return '';
        try {
            let cleanUrl = url.split('?')[0].split('#')[0];
            cleanUrl = decodeURIComponent(cleanUrl);
            const segments = cleanUrl.split('/');
            const lastSegment = segments[segments.length - 1];
            if (!lastSegment) return '';
            const dotIndex = lastSegment.lastIndexOf('.');
            if (dotIndex === -1) return '';
            return lastSegment.substring(dotIndex + 1).toLowerCase();
        } catch (e) {
            return '';
        }
    }

    getExtensionFromFileName(fileName) {
        if (!fileName) return '';
        const dotIndex = fileName.lastIndexOf('.');
        if (dotIndex === -1) return '';
        return fileName.substring(dotIndex + 1).toLowerCase();
    }

    getFileExtension(fileUrl, fileName) {
        const urlExt = this.getExtensionFromUrl(fileUrl);
        if (urlExt) return urlExt;
        const nameExt = this.getExtensionFromFileName(fileName);
        if (nameExt) return nameExt;
        return '';
    }

    getFileType(fileUrl, fileName) {
        const ext = this.getFileExtension(fileUrl, fileName);
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'];
        const pdfExts = ['pdf'];
        const textExts = ['txt', 'csv', 'log', 'md', 'json', 'xml', 'yaml', 'yml', 'ini', 'cfg', 'conf'];
        const codeExts = ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'ts', 'jsx', 'tsx', 'vue', 'sql', 'sh', 'bash'];
        const videoExts = ['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'];
        const audioExts = ['mp3', 'wav', 'flac', 'aac'];

        if (!ext) return 'other';
        if (imageExts.includes(ext)) return 'image';
        if (pdfExts.includes(ext)) return 'pdf';
        if (textExts.includes(ext)) return 'text';
        if (codeExts.includes(ext)) return 'code';
        if (videoExts.includes(ext)) return 'video';
        if (audioExts.includes(ext)) return 'audio';
        return 'other';
    }

    getDisplayFileName(fileUrl, fileName) {
        if (fileName && fileName.trim()) return fileName.trim();
        try {
            let cleanUrl = (fileUrl || '').split('?')[0].split('#')[0];
            cleanUrl = decodeURIComponent(cleanUrl);
            const segments = cleanUrl.split('/');
            const lastSegment = segments[segments.length - 1];
            if (lastSegment) return lastSegment;
        } catch (e) {}
        return 'File';
    }

    normalizeResources(resources) {
        if (!resources || !Array.isArray(resources)) return [];

        return resources.map(resource => {
            if (resource.name && resource.size && resource.url) return resource;

            const fileUrl = resource.file || resource.url || '';
            const fileName = resource.name || this.getDisplayFileName(fileUrl, '');
            const fileType = resource.type || this.getFileType(fileUrl, fileName);
            const fileSize = resource.size || 'Unknown size';

            return {
                name: fileName,
                size: fileSize,
                type: fileType,
                url: fileUrl
            };
        });
    }

    getTypeIcon(type) {
        const icons = {
            video: '<i class="fas fa-play-circle"></i>',
            article: '<i class="fas fa-file-lines"></i>',
            quiz: '<i class="fas fa-circle-question"></i>',
            assignment: '<i class="fas fa-tasks"></i>',
            file: '<i class="fas fa-file"></i>',
            live_session: '<i class="fas fa-video"></i>',
            coding_exercise: '<i class="fas fa-code"></i>'
        };
        return icons[type] || '<i class="fas fa-file"></i>';
    }

    getTypeLabel(type) {
        const labels = {
            video: 'Video',
            article: 'Article',
            quiz: 'Quiz',
            assignment: 'Assignment',
            file: 'File',
            live_session: 'Live Session',
            coding_exercise: 'Coding Exercise'
        };
        return labels[type] || this.capitalize(type);
    }

    getQuestionTypeLabel(type) {
        const labels = {
            'single_choice': 'Single Choice',
            'multiple_choice': 'Multiple Choice',
            'true_false': 'True / False',
            'short_answer': 'Short Answer'
        };
        return labels[type] || 'Question';
    }

    getFileTypeIcon(fileType) {
        const icons = {
            image: 'fa-file-image',
            pdf: 'fa-file-pdf',
            text: 'fa-file-alt',
            code: 'fa-file-code',
            video: 'fa-file-video',
            audio: 'fa-file-audio',
            other: 'fa-file'
        };
        return icons[fileType] || 'fa-file';
    }

    getFileTypeLabel(fileType) {
        const labels = {
            image: 'Image File',
            pdf: 'PDF Document',
            text: 'Text File',
            code: 'Code File',
            video: 'Video File',
            audio: 'Audio File',
            other: 'File'
        };
        return labels[fileType] || 'File';
    }

    getResourceIconClass(type) {
        const icons = {
            pdf: 'fa-file-pdf',
            code: 'fa-file-code',
            zip: 'fa-file-archive',
            image: 'fa-file-image',
            video: 'fa-file-video',
            file: 'fa-file'
        };
        return icons[type] || 'fa-file';
    }

    capitalize(str) {
        return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
    }

    escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#1F2937;color:#FFF;padding:12px 24px;border-radius:8px;font-size:0.85rem;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,0.3);transition:opacity 0.3s;';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }

    // ============================================
    // DUMMY DATA GENERATORS (Fallback)
    // ============================================

    getDummyCurriculum(courseId) {
        return {};
    }

    getDummyLessonContent(lessonId) {
        const curriculum = this.getDummyCurriculum(this.courseId);
        let lesson = null;

        for (const section of curriculum.sections) {
            const found = section.lessons.find(l => l.id === lessonId);
            if (found) {
                lesson = { ...found };
                break;
            }
        }

        if (!lesson) {
            return {
                id: lessonId,
                title: `Lesson ${lessonId}`,
                type: 'article',
                article_content: '<p>Lesson content not available.</p>'
            };
        }

        return lesson;
    }
}

// ============================================
// GLOBAL FUNCTIONS AND INITIALIZATION
// ============================================

let previewInstance;

function toggleSection(header) {
    if (window.previewInstance) {
        window.previewInstance.toggleSection(header);
    }
}

function navigateToLesson(id) {
    if (window.previewInstance) {
        window.previewInstance.navigateToLessonById(id);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    previewInstance = new InstructorCoursePreview();

    // Expose instance globally for onclick handlers
    window.previewInstance = previewInstance;
});
