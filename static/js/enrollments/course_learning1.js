// ============================================
// LEARNING INTERFACE PAGE CONTROLLER
// ============================================
const baseUrl = window.location.origin;
const auth = new Auth({
    "baseURL": window.location.origin + '/api/v1/account/auth',
    "onLogout": ()=>{window.location.href = baseUrl + '/account/auth/login'}
});

class ApiService {
    static async getEnrollmentCurriculum(enrollmentId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/course/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch enrollment course');
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Using dummy curriculum data:', error.message);
            return this.getDummyCurriculum(enrollmentId);
        }
    }

    static async getLessonContent(enrollmentId, lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch lesson content');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Using dummy lesson content:', error.message);
            return this.getDummyLessonContent(enrollmentId, lessonId);
        }
    }

    static async getVideoResumePoint(enrollmentId, lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/resume/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch video resume point');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to fetch resume point:', error.message);
            return {
                success: false,
                timestamp: 0,
                message: 'No resume point available'
            };
        }
    }

    static async saveVideoResumePoint(enrollmentId, lessonId, timestamp) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/resume/`,
                { method: "POST", body: JSON.stringify({ timestamp }) }
            );
            if (!response.ok) throw new Error('Failed to save video resume point');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to save resume point:', error.message);
            return {
                success: false,
                timestamp: timestamp,
                message: 'Failed to save resume point'
            };
        }
    }

    static async submitLessonCompletion(enrollmentId, lessonId, completionData) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/complete/`,
                { method: "POST", body: JSON.stringify(completionData) }
            );
            if (!response.ok) throw new Error('Failed to submit lesson completion');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Using dummy completion response:', error.message);
            return {
                success: false,
                completed: completionData?.completed,
                message: 'Failed to update completion status'
            };
        }
    }

    static async submitQuizAnswers(enrollmentId, lessonId, answers) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/quiz/submit/`,
                { method: "POST", body: JSON.stringify({ answers }) }
            );
            if (!response.ok) throw new Error('Failed to submit quiz answers');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to submit quiz:', error.message);
            return {
                success: false,
                message: 'Failed to submit quiz'
            };
        }
    }

    static async getQuizAttemptStatus(enrollmentId, lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/quiz/attempts/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch quiz attempt status');
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Failed to fetch quiz attempts:', error.message);
            return {
                success: true,
                attempts_used: 0,
                max_attempts: 3,
                attempts_remaining: 3,
                can_attempt: true
            };
        }
    }

    static async getAssignmentDetails(enrollmentId, lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/assignment/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch assignment details');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to fetch assignment details:', error.message);
            return {
                success: false,
                message: 'Failed to fetch assignment details'
            };
        }
    }

    static async submitAssignment(enrollmentId, lessonId, submissionText, files) {
        try {
            const formData = new FormData();
            formData.append('submission_text', submissionText);

            if (files && files.length > 0) {
                for (const file of files) {
                    formData.append('files', file);
                }
            }

            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/assignment/submit/`,
                {
                    method: "POST",
                    body: formData,
                    headers: {}
                }
            );
            if (!response.ok) throw new Error('Failed to submit assignment');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to submit assignment:', error.message);
            return {
                success: false,
                message: 'Failed to submit assignment'
            };
        }
    }

    static async getEnrollmentProgress(enrollmentId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/progress/`,
                { method: "GET" }
            );
            if (!response.ok) throw new Error('Failed to fetch enrollment progress');
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Failed to fetch progress:', error.message);
            return {
                enrollmentId: enrollmentId,
                overallProgress: 0,
                completedLessons: [],
                completedCount: 0,
                totalLessons: 12,
                bookmarkedLessons: []
            };
        }
    }

    static async toggleBookmark(enrollmentId, lessonId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/${enrollmentId}/lesson/${lessonId}/bookmark/`,
                { method: "POST" }
            );
            if (!response.ok) throw new Error('Failed to toggle bookmark');
            const data = await response.json();

            return data;
        } catch (error) {
            console.warn('Failed to toggle bookmark:', error.message);
            return {
                success: false,
                message: 'Failed to update bookmark'
            };
        }
    }

    // ============================================
    // DUMMY DATA GENERATORS (For testing only)
    // ============================================

    static getDummyCurriculum(enrollmentId) {
        return {
            enrollmentId: enrollmentId,
            courseId: 'python-data-science',
            courseTitle: 'Python for Data Science',
            totalLessons: 12,
            sections: [
                {
                    id: 1,
                    title: 'Introduction to Python',
                    lessons: [
                        {
                            id: 1,
                            title: 'Getting Started with Python',
                            type: 'video',
                            duration: '15 min',
                            duration_seconds: 900,
                            order: 1,
                            preview: false,
                            has_resources: true,
                            completion_criteria: {
                                criteria_type: 'watch_video',
                                video_watch_percentage: 90
                            },
                            videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
                            description: 'Learn the basics of Python programming language including installation, syntax, and running your first program. This comprehensive introduction covers everything you need to get started with Python development.',
                            resources: [
                                { name: 'Python Setup Guide.pdf', size: '1.2 MB', type: 'pdf', url: '#' },
                                { name: 'Code Examples.zip', size: '500 KB', type: 'zip', url: '#' }
                            ],
                            transcript: [
                                { time: '00:00', text: 'Welcome to Python for Data Science. In this lesson, we will cover the basics of Python programming.' },
                                { time: '00:30', text: 'First, let us install Python on your system. You can download it from python.org.' },
                                { time: '01:00', text: 'Once installed, open your terminal and type python to start the interpreter.' },
                                { time: '01:30', text: 'Let us write our first program: print("Hello, World!")' },
                                { time: '02:00', text: 'Python is known for its simple and readable syntax.' }
                            ]
                        },
                        {
                            id: 2,
                            title: 'Python Variables and Data Types',
                            type: 'article',
                            duration: '10 min',
                            duration_seconds: 600,
                            order: 2,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'read_article',
                                article_scroll_percentage: 90
                            },
                            description: 'Master Python variables, data types, and type conversion with practical examples.',
                            articleContent: '<h2>Python Variables</h2><p>Variables are used to store data values in Python.</p><p>Python has several built-in data types including integers, floats, strings, and booleans.</p><p>Understanding variables is fundamental to programming in Python.</p><p>Let\'s explore more about variables and data types in this comprehensive guide.</p><p>You\'ll learn how to declare variables, assign values, and perform operations.</p><p>By the end of this article, you\'ll have a solid understanding of Python\'s type system.</p><p>Variables can be reassigned to different values throughout your program.</p><p>Python uses dynamic typing, which means you don\'t need to declare variable types explicitly.</p><p>This makes Python code more concise and easier to read.</p>'
                        },
                        {
                            id: 3,
                            title: 'Control Flow Quiz',
                            type: 'quiz',
                            duration: '20 min',
                            duration_seconds: 1200,
                            order: 3,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'pass_quiz',
                                quiz_passing_score: 60
                            },
                            description: 'Test your knowledge of Python control flow with this comprehensive quiz.',
                            quizData: {
                                passScore: 60,
                                max_attempts: 3,
                                questions: [
                                    {
                                        id: 22,
                                        text: 'What is the output of 2 + 2?',
                                        question_type: 'single_choice',
                                        choices: [
                                            {id: 1, text: '3'},
                                            {id: 2, text: '4'},
                                            {id: 3, text: '5'},
                                            {id: 4, text: '6'}
                                        ],
                                        points: 1,
                                        explanation: 'Basic arithmetic operation'
                                    },
                                    {
                                        id: 23,
                                        text: 'What does ORM stand for in Django?',
                                        question_type: 'short_answer',
                                        points: 2,
                                        explanation: 'Object-Relational Mapping'
                                    },
                                    {
                                        id: 24,
                                        text: 'Python is an interpreted language.',
                                        question_type: 'true_false',
                                        points: 1,
                                        explanation: 'Python code is executed line by line'
                                    },
                                    {
                                        id: 25,
                                        text: 'Which of the following are valid string formatting methods?',
                                        question_type: 'multiple_choice',
                                        choices: [
                                            {id: 1, text: 'str()'},
                                            {id: 2, text: 'format()'},
                                            {id: 3, text: 'double quotation marks'},
                                            {id: 4, text: 'f-strings'}
                                        ],
                                        points: 3,
                                        explanation: 'Multiple ways to format strings in Python'
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    id: 2,
                    title: 'Data Structures',
                    lessons: [
                        {
                            id: 4,
                            title: 'Lists and Tuples',
                            type: 'video',
                            duration: '18 min',
                            duration_seconds: 1080,
                            order: 1,
                            preview: false,
                            has_resources: true,
                            completion_criteria: {
                                criteria_type: 'watch_video',
                                video_watch_percentage: 90
                            },
                            videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
                            description: 'Deep dive into Python lists and tuples - creation, manipulation, and best practices.',
                            resources: [
                                { name: 'Lists Cheatsheet.pdf', size: '800 KB', type: 'pdf', url: '#' }
                            ],
                            transcript: [
                                { time: '00:00', text: 'In this lesson, we will explore lists and tuples in Python.' },
                                { time: '00:45', text: 'Lists are mutable sequences, while tuples are immutable.' }
                            ]
                        },
                        {
                            id: 5,
                            title: 'Dictionaries Deep Dive',
                            type: 'article',
                            duration: '12 min',
                            duration_seconds: 720,
                            order: 2,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'manual'
                            },
                            description: 'Learn dictionary operations, methods, and real-world use cases.',
                            articleContent: '<h2>Python Dictionaries</h2><p>Dictionaries are key-value pairs in Python.</p><p>They are mutable and unordered in older Python versions.</p><p>Learn how to create, access, and manipulate dictionaries.</p><p>Dictionary comprehension is a powerful feature in Python.</p><p>Master dictionary methods for efficient data handling.</p><p>Dictionaries are optimized for retrieving values when you know the key.</p><p>They are one of the most commonly used data structures in Python.</p><p>Understanding dictionaries is essential for working with JSON data.</p><p>Python dictionaries preserve insertion order in Python 3.7+.</p>'
                        },
                        {
                            id: 6,
                            title: 'Data Structures Quiz',
                            type: 'quiz',
                            duration: '15 min',
                            duration_seconds: 900,
                            order: 3,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'pass_quiz',
                                quiz_passing_score: 70
                            },
                            description: 'Evaluate your understanding of Python data structures.',
                            quizData: {
                                passScore: 70,
                                max_attempts: 2,
                                questions: [
                                    {
                                        id: 26,
                                        text: 'Which data structure is immutable?',
                                        question_type: 'single_choice',
                                        choices: [
                                            {id: 1, text: 'List'},
                                            {id: 2, text: 'Tuple'},
                                            {id: 3, text: 'Dictionary'},
                                            {id: 4, text: 'Set'}
                                        ],
                                        points: 1,
                                        explanation: 'Tuples cannot be modified after creation'
                                    },
                                    {
                                        id: 27,
                                        text: 'How do you create an empty dictionary?',
                                        question_type: 'short_answer',
                                        points: 2,
                                        explanation: 'Using {} or dict()'
                                    },
                                    {
                                        id: 28,
                                        text: 'Lists preserve insertion order.',
                                        question_type: 'true_false',
                                        points: 1,
                                        explanation: 'Lists maintain the order of elements'
                                    },
                                    {
                                        id: 29,
                                        text: 'Which operations are valid on sets?',
                                        question_type: 'multiple_choice',
                                        choices: [
                                            {id: 1, text: 'union'},
                                            {id: 2, text: 'intersection'},
                                            {id: 3, text: 'difference'},
                                            {id: 4, text: 'indexing'}
                                        ],
                                        points: 3,
                                        explanation: 'Sets support mathematical operations'
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    id: 3,
                    title: 'Advanced Topics',
                    lessons: [
                        {
                            id: 7,
                            title: 'Object-Oriented Programming',
                            type: 'video',
                            duration: '25 min',
                            duration_seconds: 1500,
                            order: 1,
                            preview: false,
                            has_resources: true,
                            completion_criteria: {
                                criteria_type: 'watch_video',
                                video_watch_percentage: 85
                            },
                            videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
                            description: 'Master object-oriented programming concepts in Python including classes, inheritance, and polymorphism.',
                            resources: [
                                { name: 'OOP Examples.zip', size: '2.1 MB', type: 'zip', url: '#' },
                                { name: 'Class Diagrams.pdf', size: '1.5 MB', type: 'pdf', url: '#' },
                                { name: 'Reference Guide.docx', size: '900 KB', type: 'zip', url: '#' }
                            ]
                        },
                        {
                            id: 8,
                            title: 'Exception Handling',
                            type: 'article',
                            duration: '15 min',
                            duration_seconds: 900,
                            order: 2,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'read_article',
                                article_scroll_percentage: 90
                            },
                            description: 'Learn to handle errors gracefully with try-except blocks and custom exceptions.',
                            articleContent: '<h2>Exception Handling</h2><p>Learn to handle errors gracefully in Python.</p><p>Try, except, finally blocks are essential for robust code.</p><p>Custom exceptions can be created for specific needs.</p><p>Proper error handling makes applications more reliable.</p><p>Understanding exception hierarchy is important for catching specific errors.</p><p>The finally block always executes regardless of whether an exception occurs.</p><p>You can raise exceptions manually using the raise keyword.</p><p>Exception handling improves user experience by preventing crashes.</p>'
                        },
                        {
                            id: 9,
                            title: 'File Operations',
                            type: 'file',
                            duration: '10 min',
                            duration_seconds: 600,
                            order: 3,
                            preview: false,
                            has_resources: true,
                            completion_criteria: {
                                criteria_type: 'manual'
                            },
                            description: 'Download and review Python file operation resources and cheatsheets.',
                            file_url: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
                            file_name: 'Python Cheatsheet.pdf',
                            resources: [
                                { name: 'Python Cheatsheet.pdf', size: '2.4 MB', type: 'pdf', url: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf' },
                                { name: 'Code Examples.zip', size: '1.1 MB', type: 'zip', url: '#' },
                                { name: 'Reference Guide.docx', size: '850 KB', type: 'zip', url: '#' }
                            ]
                        },
                        {
                            id: 10,
                            title: 'Final Project',
                            type: 'assignment',
                            duration: '60 min',
                            duration_seconds: 3600,
                            order: 4,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'submit_assignment'
                            },
                            description: 'Build a complete data analysis project and submit for instructor review.',
                            assignmentData: {
                                instructions: 'Build a data analysis project using Python. Analyze a dataset of your choice and present your findings with visualizations.',
                                maxScore: 100,
                                dueDate: '2024-12-31T23:59:59Z',
                                allowLateSubmission: false,
                                maxAttempts: 3,
                                acceptedFileTypes: 'pdf,docx,zip,py',
                                maxFileSizeMB: 50
                            }
                        },
                        {
                            id: 11,
                            title: 'Live Q&A Session',
                            type: 'live_session',
                            duration: '45 min',
                            duration_seconds: 2700,
                            order: 5,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'manual'
                            },
                            description: 'Join the live Q&A session to get your questions answered by instructors.'
                        },
                        {
                            id: 12,
                            title: 'Coding Challenge',
                            type: 'coding_exercise',
                            duration: '30 min',
                            duration_seconds: 1800,
                            order: 6,
                            preview: false,
                            has_resources: false,
                            completion_criteria: {
                                criteria_type: 'manual'
                            },
                            description: 'Complete the hands-on coding challenge to practice your Python skills.'
                        }
                    ]
                }
            ]
        };
    }

    static getDummyLessonContent(enrollmentId, lessonId) {
        const curriculum = this.getDummyCurriculum(enrollmentId);
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
                description: 'Lesson content not available.',
                articleContent: '<p>Lesson content not available.</p>',
                video_progress: { timestamp: 0 }
            };
        }

        return lesson;
    }
}

class LearningInterface {
    constructor() {
        this.enrollmentId = this.getEnrollmentIdFromUrl();
        this.courseId = null;
        this.currentLessonId = null;
        this.currentLessonType = 'video';
        this.currentSectionIndex = 0;
        this.currentLessonIndex = 0;
        this.currentQuizIndex = 0;
        this.quizScore = 0;
        this.sidebarOpen = true;
        this.courseData = null;
        this.progressData = null;
        this.bookmarkedLessons = new Set();
        this.activeTab = 'overview';
        this.isInitialLoad = true;
        this.courseCompleted = false;
        this.certificateData = null;

        this.videoPlayer = null;
        this.videoWatchPercentage = 0;
        this.videoCompletionThreshold = 90;
        this.videoAutoCompleted = false;
        this.videoTrackingInterval = null;
        this.lastVideoTimeUpdate = 0;
        this.videoProgressBar = null;
        this.videoProgressFill = null;
        this.videoProgressBuffered = null;
        this.videoProgressHover = null;
        this.videoProgressThumb = null;
        this.isDraggingProgress = false;
        this.hideControlsTimeout = null;
        this.controlsVisible = true;
        this.videoResumeTimestamp = 0;

        this.watchedSegments = [];
        this.currentSegmentStart = 0;
        this.lastSaveTime = 0;
        this.saveInterval = 5000;
        this.seekThreshold = 2;
        this.isSeeking = false;
        this.videoMetadataLoaded = false;
        this.videoResumeApplied = false;
        this.videoSaveQueue = [];
        this.isSavingVideo = false;
        this.maxWatchedSegments = 100;
        this.videoCompletionMinWatchTime = 60;
        this.videoResumeLoading = false;
        this.videoResumeLoaded = false;

        this.isCompleting = false;

        this.quizUserAnswers = [];
        this.quizQuestionsWithoutCorrect = [];
        this.isQuizSubmitting = false;
        this.quizResultData = null;
        this.quizCompleted = false;
        this.quizPhase = 'answering';
        this.quizAttemptsUsed = 0;
        this.maxQuizAttempts = 3;
        this.quizAttemptsRemaining = 3;
        this.quizBestScore = 0;
        this.quizCanAttempt = true;
        this.quizResultsCache = {};

        this.assignmentData = null;
        this.assignmentSubmissions = [];
        this.isAssignmentSubmitting = false;
        this.selectedFiles = [];

        this.fileModal = null;
        this.fileModalContent = null;

        this.articleScrollPercentage = 0;
        this.articleScrollThreshold = 90;
        this.articleAutoCompleted = false;
        this.articleScrollTrackingActive = false;
        this.articleContentElement = null;
        this.articleCompletionInProgress = false;

        this.init();
    }

    getEnrollmentIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/enrollment\/([^/]+)\/learn/);
        return match ? match[1] : 'ENR-001';
    }

    getLessonIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/enrollment\/([^/]+)\/learn\/(\d+)/);
        return match ? parseInt(match[2]) : null;
    }

    getCourseIdFromUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get('course') || null;
    }

    getTabFromUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get('tab') || null;
    }

    async init() {
        this.bindEvents();
        this.initializeVideoPlayer();
        this.setupVideoProgressBar();
        this.createSpeedMenu();
        this.createFileViewerModal();
        await this.loadCourseStructure();
        await this.loadProgressData();
        this.renderSidebar();
        await this.determineStartingLesson();
        this.handleResponsiveSidebar();

        const tabParam = this.getTabFromUrl();
        if (tabParam && ['overview', 'resources'].includes(tabParam)) {
            this.switchTab(tabParam, true);
        }

        this.setupVideoTracking();

        window.addEventListener('resize', () => this.handleResponsiveSidebar());

        setInterval(() => this.saveProgressToBackend(), 15000);

        window.addEventListener('beforeunload', () => {
            this.stopVideoTracking();
            this.stopArticleScrollTracking();
            this.saveVideoProgressImmediate();
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.saveVideoProgressImmediate();
            }
        });

        this.isInitialLoad = false;
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

        const mainComplete = document.getElementById('mainMarkCompleteBtn');
        if (mainComplete) mainComplete.addEventListener('click', () => this.handleManualCompletion());

        const articleComplete = document.getElementById('articleMarkCompleteBtn');
        if (articleComplete) articleComplete.addEventListener('click', () => this.handleManualCompletion());

        const mobileComplete = document.getElementById('mobileMarkCompleteBtn');
        if (mobileComplete) mobileComplete.addEventListener('click', () => this.handleManualCompletion());

        const videoPlay = document.getElementById('videoBigPlayBtn');
        if (videoPlay) videoPlay.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleVideoPlay();
        });

        const playPause = document.getElementById('playPauseBtn');
        if (playPause) playPause.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleVideoPlay();
        });

        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) fullscreenBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleFullscreen();
        });

        const speedBtn = document.getElementById('speedBtn');
        if (speedBtn) speedBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleSpeedMenu();
        });

        const videoContainer = document.getElementById('videoContainer');
        if (videoContainer) {
            videoContainer.addEventListener('click', (e) => {
                if (!e.target.closest('button') && !e.target.closest('.video-controls') && !e.target.closest('.speed-menu')) {
                    this.toggleVideoPlay();
                }
            });

            videoContainer.addEventListener('mousemove', () => this.showVideoControls());
            videoContainer.addEventListener('mouseleave', () => this.hideVideoControls());
        }

        document.addEventListener('fullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('webkitfullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('mozfullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('MSFullscreenChange', () => this.onFullscreenChange());

        document.addEventListener('keydown', (e) => {
            if (this.currentLessonType !== 'video') return;
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    this.toggleVideoPlay();
                    break;
                case 'ArrowLeft':
                    if (!e.ctrlKey) {
                        e.preventDefault();
                        this.skipVideo(-5);
                    }
                    break;
                case 'ArrowRight':
                    if (!e.ctrlKey) {
                        e.preventDefault();
                        this.skipVideo(5);
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.adjustVolume(0.1);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.adjustVolume(-0.1);
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    this.toggleMute();
                    break;
            }
        });

        const bookmarkToggle = document.getElementById('bookmarkToggleBtn');
        if (bookmarkToggle) bookmarkToggle.addEventListener('click', () => this.toggleBookmark());

        const resourcesToggle = document.getElementById('resourcesToggleBtn');
        if (resourcesToggle) resourcesToggle.addEventListener('click', () => this.switchTab('resources'));

        const lessonTabs = document.querySelectorAll('.lesson-tab');
        lessonTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        const userAvatar = document.getElementById('userAvatar');
        if (userAvatar) {
            userAvatar.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = document.getElementById('userDropdown');
                if (dropdown) dropdown.classList.toggle('visible');
            });
        }

        document.addEventListener('click', () => {
            const dropdown = document.getElementById('userDropdown');
            if (dropdown) dropdown.classList.remove('visible');
        });

        this.setupQuizEventDelegation();
        this.setupAssignmentEventDelegation();
    }

    setupAssignmentEventDelegation() {
        const assignmentSection = document.getElementById('assignmentSection');
        if (!assignmentSection) return;

        if (this._assignmentClickHandler) assignmentSection.removeEventListener('click', this._assignmentClickHandler);
        this._assignmentClickHandler = (e) => {
            const button = e.target.closest('button');
            if (!button) return;
            switch (button.id) {
                case 'assignmentSubmitBtn': e.preventDefault(); this.handleAssignmentSubmit(); break;
                case 'assignmentFileInputBtn': e.preventDefault(); this.triggerFileInput(); break;
            }
        };
        assignmentSection.addEventListener('click', this._assignmentClickHandler);

        if (this._assignmentChangeHandler) assignmentSection.removeEventListener('change', this._assignmentChangeHandler);
        this._assignmentChangeHandler = (e) => {
            if (e.target.id === 'assignmentFileInput') {
                this.handleFileSelection(e.target.files);
            }
        };
        assignmentSection.addEventListener('change', this._assignmentChangeHandler);
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
            videoElement.crossOrigin = 'anonymous';
            videoElement.style.cssText = 'width:100%;height:100%;object-fit:contain;background:#000;border-radius:8px;cursor:pointer;display:block;';
            videoElement.setAttribute('playsinline', '');
            videoElement.setAttribute('webkit-playsinline', '');
            videoElement.setAttribute('x-webkit-airplay', 'allow');

            const videoOverlay = document.getElementById('videoOverlay');
            if (videoOverlay) {
                videoContainer.insertBefore(videoElement, videoOverlay);
            } else {
                videoContainer.appendChild(videoElement);
            }
        }

        this.videoPlayer = videoElement;

        videoElement.addEventListener('timeupdate', () => {
            this.updateVideoTimeDisplay();
            this.updateProgressBar();
        });

        videoElement.addEventListener('loadedmetadata', () => {
            this.videoMetadataLoaded = true;
            this.updateVideoTimeDisplay();
            this.updateProgressBar();
            this.applyVideoResumePoint();
        });

        videoElement.addEventListener('play', () => this.onVideoPlay());
        videoElement.addEventListener('pause', () => this.onVideoPause());
        videoElement.addEventListener('ended', () => this.onVideoEnded());
        videoElement.addEventListener('waiting', () => this.onVideoWaiting());
        videoElement.addEventListener('canplay', () => this.onVideoCanPlay());
        videoElement.addEventListener('error', (e) => this.onVideoError(e));

        videoElement.addEventListener('seeking', () => {
            this.isSeeking = true;
        });

        videoElement.addEventListener('seeked', () => {
            this.isSeeking = false;
            this.handleVideoSeekComplete();
        });
    }

    setupVideoProgressBar() {
        const videoControls = document.getElementById('videoControls');
        if (!videoControls) return;

        let progressContainer = videoControls.querySelector('.video-progress-container');
        if (progressContainer) return;

        progressContainer = document.createElement('div');
        progressContainer.className = 'video-progress-container';
        progressContainer.style.cssText = 'width:100%;height:5px;background:rgba(255,255,255,0.15);cursor:pointer;position:relative;margin-bottom:8px;border-radius:3px;transition:height 0.2s ease;';

        const progressFill = document.createElement('div');
        progressFill.className = 'video-progress-fill';
        progressFill.style.cssText = 'height:100%;background:#8B5CF6;border-radius:3px;width:0%;transition:width 0.1s linear;position:relative;';

        const progressBuffered = document.createElement('div');
        progressBuffered.className = 'video-progress-buffered';
        progressBuffered.style.cssText = 'position:absolute;top:0;left:0;height:100%;background:rgba(255,255,255,0.1);border-radius:3px;width:0%;';

        const progressHover = document.createElement('div');
        progressHover.className = 'video-progress-hover';
        progressHover.style.cssText = 'position:absolute;top:0;left:0;height:100%;background:rgba(255,255,255,0.2);border-radius:3px;width:0%;display:none;';

        const progressThumb = document.createElement('div');
        progressThumb.className = 'video-progress-thumb';
        progressThumb.style.cssText = 'position:absolute;top:50%;transform:translate(-50%,-50%);width:14px;height:14px;background:#8B5CF6;border-radius:50%;display:none;box-shadow:0 0 4px rgba(0,0,0,0.5);';

        progressFill.appendChild(progressThumb);
        progressContainer.appendChild(progressBuffered);
        progressContainer.appendChild(progressHover);
        progressContainer.appendChild(progressFill);

        videoControls.insertBefore(progressContainer, videoControls.firstChild);

        this.videoProgressBar = progressContainer;
        this.videoProgressFill = progressFill;
        this.videoProgressBuffered = progressBuffered;
        this.videoProgressHover = progressHover;
        this.videoProgressThumb = progressThumb;

        progressContainer.addEventListener('mousedown', (e) => this.startProgressDrag(e));
        progressContainer.addEventListener('mousemove', (e) => this.updateProgressHover(e));
        progressContainer.addEventListener('mouseleave', () => {
            if (this.videoProgressHover) this.videoProgressHover.style.display = 'none';
            if (this.videoProgressThumb) this.videoProgressThumb.style.display = 'none';
        });
        progressContainer.addEventListener('mouseenter', () => {
            if (this.videoProgressHover) this.videoProgressHover.style.display = 'block';
            if (this.videoProgressThumb) this.videoProgressThumb.style.display = 'block';
        });

        document.addEventListener('mousemove', (e) => this.onProgressDrag(e));
        document.addEventListener('mouseup', () => this.endProgressDrag());

        progressContainer.addEventListener('touchstart', (e) => this.startProgressDrag(e.touches[0]));
        document.addEventListener('touchmove', (e) => this.onProgressDrag(e.touches[0]));
        document.addEventListener('touchend', () => this.endProgressDrag());
    }

    startProgressDrag(e) {
        this.isDraggingProgress = true;
        this.seekVideo(e);
    }

    onProgressDrag(e) {
        if (!this.isDraggingProgress) return;
        this.seekVideo(e);
    }

    endProgressDrag() {
        this.isDraggingProgress = false;
    }

    seekVideo(e) {
        if (!this.videoProgressBar || !this.videoPlayer) return;
        const rect = this.videoProgressBar.getBoundingClientRect();
        const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        if (this.videoPlayer.duration) {
            this.videoPlayer.currentTime = pos * this.videoPlayer.duration;
        }
    }

    updateProgressHover(e) {
        if (!this.videoProgressBar || !this.videoProgressHover || !this.videoProgressThumb) return;
        const rect = this.videoProgressBar.getBoundingClientRect();
        const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const percent = pos * 100;
        this.videoProgressHover.style.width = percent + '%';
        this.videoProgressHover.style.display = 'block';
        this.videoProgressThumb.style.left = percent + '%';
        this.videoProgressThumb.style.display = 'block';
    }

    updateProgressBar() {
        if (!this.videoPlayer || !this.videoProgressFill || !this.videoProgressBuffered) return;

        const video = this.videoPlayer;
        if (video.duration) {
            const percent = (video.currentTime / video.duration) * 100;
            this.videoProgressFill.style.width = percent + '%';

            if (video.buffered.length > 0) {
                const bufferedEnd = video.buffered.end(video.buffered.length - 1);
                const bufferedPercent = (bufferedEnd / video.duration) * 100;
                this.videoProgressBuffered.style.width = bufferedPercent + '%';
            }
        }
    }

    createSpeedMenu() {
        const speedBtn = document.getElementById('speedBtn');
        if (!speedBtn) return;

        let speedMenu = document.querySelector('.speed-menu');
        if (speedMenu) return;

        speedMenu = document.createElement('div');
        speedMenu.className = 'speed-menu';
        speedMenu.style.cssText = 'position:absolute;bottom:50px;left:50%;transform:translateX(-50%);background:#1F2937;border:1px solid #2A2A3E;border-radius:8px;padding:4px;display:none;z-index:100;min-width:100px;box-shadow:0 8px 24px rgba(0,0,0,0.4);';

        const speeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
        speeds.forEach(speed => {
            const item = document.createElement('div');
            item.textContent = speed === 1 ? 'Normal' : speed + 'x';
            item.style.cssText = 'padding:8px 16px;color:#AAA;cursor:pointer;border-radius:4px;font-size:0.85rem;transition:all 0.15s ease;';
            if (speed === 1) item.style.color = '#8B5CF6';
            item.addEventListener('mouseenter', () => item.style.background = 'rgba(139,92,246,0.15)');
            item.addEventListener('mouseleave', () => item.style.background = 'transparent');
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.videoPlayer) {
                    this.videoPlayer.playbackRate = speed;
                    speedBtn.textContent = speed === 1 ? '1x' : speed + 'x';
                    speedMenu.style.display = 'none';
                    speedMenu.querySelectorAll('div').forEach(d => d.style.color = '#AAA');
                    item.style.color = '#8B5CF6';
                }
            });
            speedMenu.appendChild(item);
        });

        speedBtn.parentElement.style.position = 'relative';
        speedBtn.parentElement.appendChild(speedMenu);
    }

    createFileViewerModal() {
        const existingModal = document.getElementById('fileViewerModal');
        if (existingModal) existingModal.remove();

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

        document.getElementById('fileViewerCloseBtn').addEventListener('click', () => this.closeFileViewer());

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.fileModal.style.display === 'block') {
                this.closeFileViewer();
            }
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeFileViewer();
        });
    }

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
            const possibleDoubleExt = lastSegment.substring(dotIndex - 4, dotIndex);
            if (possibleDoubleExt.includes('.')) {
                const doubleDotIndex = possibleDoubleExt.lastIndexOf('.') + dotIndex - 4;
                const doubleExt = lastSegment.substring(doubleDotIndex + 1).toLowerCase();
                const knownDoubleExts = ['tar.gz', 'tar.bz2', 'tar.xz'];
                if (knownDoubleExts.includes(doubleExt)) return doubleExt;
            }
            return lastSegment.substring(dotIndex + 1).toLowerCase();
        } catch (e) { return ''; }
    }

    getExtensionFromFileName(fileName) {
        if (!fileName) return '';
        const dotIndex = fileName.lastIndexOf('.');
        if (dotIndex === -1) return '';
        const possibleDoubleExt = fileName.substring(dotIndex - 4, dotIndex);
        if (possibleDoubleExt.includes('.')) {
            const doubleDotIndex = possibleDoubleExt.lastIndexOf('.') + dotIndex - 4;
            const doubleExt = fileName.substring(doubleDotIndex + 1).toLowerCase();
            const knownDoubleExts = ['tar.gz', 'tar.bz2', 'tar.xz'];
            if (knownDoubleExts.includes(doubleExt)) return doubleExt;
        }
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

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        if (isNaN(bytes) || bytes < 0) return 'Unknown size';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) { size /= 1024; unitIndex++; }
        if (size % 1 === 0) return size + ' ' + units[unitIndex];
        return size.toFixed(1) + ' ' + units[unitIndex];
    }

    getResourceTypeFromFile(fileUrl, fileName) {
        const fileType = this.getFileType(fileUrl, fileName);
        switch(fileType) {
            case 'pdf': return 'pdf';
            case 'image': return 'image';
            case 'video': return 'video';
            case 'code': return 'code';
            case 'text': return 'code';
            case 'audio': return 'video';
            default: return 'zip';
        }
    }

    normalizeResources(resources) {
        if (!resources || !Array.isArray(resources)) return [];
        return resources.map(resource => {
            if (resource.name && resource.size && resource.type) return resource;
            const fileUrl = resource.file || resource.url || '';
            const fileSize = resource.file_size || resource.size || 0;
            const fileName = this.getDisplayFileName(fileUrl, '');
            const formattedSize = typeof fileSize === 'string' ? fileSize : this.formatFileSize(fileSize);
            const type = resource.type || this.getResourceTypeFromFile(fileUrl, fileName);
            return { name: fileName, size: formattedSize, type: type, url: fileUrl };
        });
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
        switch(fileType) {
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
                    try { const response = await fetch(fileUrl); const text = await response.text(); const preEl = document.getElementById('textFileContent'); if (preEl) preEl.textContent = text; }
                    catch(e) { const preEl = document.getElementById('textFileContent'); if (preEl) preEl.innerHTML = '<span style="color:#EF4444;">Failed to load file content</span>'; }
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
            this.fileModalContent.innerHTML = '';
            document.body.style.overflow = '';
        }
    }

    toggleVideoPlay() {
        const video = this.videoPlayer;
        if (!video) return;
        if (video.paused || video.ended) {
            video.play().then(() => this.onVideoPlay()).catch(err => { console.error('Video play failed:', err); this.showToast('Unable to play video. Check the source URL.'); });
        } else { video.pause(); }
    }

    onVideoPlay() {
        const overlay = document.getElementById('videoOverlay');
        const playBtn = document.getElementById('playPauseBtn');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');
        if (overlay) { overlay.classList.add('playing'); overlay.style.opacity = '0'; overlay.style.pointerEvents = 'none'; }
        if (bigPlayBtn) { bigPlayBtn.style.opacity = '0'; bigPlayBtn.style.pointerEvents = 'none'; }
        if (playBtn) playBtn.innerHTML = '<i class="fas fa-pause"></i>';
        this.startControlsAutoHide();

        if (!this.isSeeking) {
            this.currentSegmentStart = this.videoPlayer.currentTime;
        }
    }

    onVideoPause() {
        const overlay = document.getElementById('videoOverlay');
        const playBtn = document.getElementById('playPauseBtn');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');
        if (overlay) { overlay.classList.remove('playing'); overlay.style.opacity = '1'; overlay.style.pointerEvents = 'auto'; }
        if (bigPlayBtn) { bigPlayBtn.style.opacity = '1'; bigPlayBtn.style.pointerEvents = 'auto'; }
        if (playBtn) playBtn.innerHTML = '<i class="fas fa-play"></i>';
        this.showVideoControls(); this.stopControlsAutoHide();

        this.endCurrentWatchSegment();
    }

    onVideoEnded() {
        const playBtn = document.getElementById('playPauseBtn');
        const overlay = document.getElementById('videoOverlay');
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');
        if (playBtn) playBtn.innerHTML = '<i class="fas fa-play"></i>';
        if (overlay) { overlay.classList.remove('playing'); overlay.style.opacity = '1'; overlay.style.pointerEvents = 'auto'; }
        if (bigPlayBtn) { bigPlayBtn.innerHTML = '<i class="fas fa-redo"></i>'; bigPlayBtn.style.opacity = '1'; bigPlayBtn.style.pointerEvents = 'auto'; }
        this.stopControlsAutoHide(); this.showVideoControls();

        this.endCurrentWatchSegment();
        this.videoWatchPercentage = 100;

        if (this.videoPlayer && this.videoPlayer.duration) {
            this.addWatchedSegment(0, this.videoPlayer.duration);
        }

        const lesson = this.getCurrentLesson();
        if (lesson && this.canAutoComplete(lesson)) {
            this.markLessonComplete(true);
        }
        this.updateVideoCompletionIndicator();
    }

    onVideoWaiting() {}
    onVideoCanPlay() {
        const bigPlayBtn = document.getElementById('videoBigPlayBtn');
        if (bigPlayBtn && bigPlayBtn.querySelector('.fa-redo')) {
            bigPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    onVideoError(e) {
        console.error('Video error:', e);
        this.showToast('Error loading video. Please try again.');
    }

    toggleFullscreen() {
        const videoContainer = document.getElementById('videoContainer');
        if (!videoContainer) return;
        if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement && !document.msFullscreenElement) {
            if (videoContainer.requestFullscreen) videoContainer.requestFullscreen();
            else if (videoContainer.webkitRequestFullscreen) videoContainer.webkitRequestFullscreen();
            else if (videoContainer.mozRequestFullScreen) videoContainer.mozRequestFullScreen();
            else if (videoContainer.msRequestFullscreen) videoContainer.msRequestFullscreen();
        } else {
            if (document.exitFullscreen) document.exitFullscreen();
            else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
            else if (document.mozCancelFullScreen) document.mozCancelFullScreen();
            else if (document.msExitFullscreen) document.msExitFullscreen();
        }
    }

    onFullscreenChange() {
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const isFullscreen = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement;
        if (fullscreenBtn) fullscreenBtn.innerHTML = isFullscreen ? '<i class="fas fa-compress"></i>' : '<i class="fas fa-expand"></i>';
        const videoContainer = document.getElementById('videoContainer');
        if (videoContainer) {
            if (isFullscreen) { videoContainer.style.borderRadius = '0'; if (this.videoPlayer) this.videoPlayer.style.borderRadius = '0'; }
            else { videoContainer.style.borderRadius = '8px'; if (this.videoPlayer) this.videoPlayer.style.borderRadius = '8px'; }
        }
    }

    skipVideo(seconds) {
        if (!this.videoPlayer) return;
        this.videoPlayer.currentTime = Math.max(0, Math.min(this.videoPlayer.duration || 0, this.videoPlayer.currentTime + seconds));
        this.showToast(`${seconds > 0 ? '+' : ''}${seconds}s`);
    }

    adjustVolume(delta) {
        if (!this.videoPlayer) return;
        this.videoPlayer.volume = Math.max(0, Math.min(1, this.videoPlayer.volume + delta));
        this.showToast(`Volume: ${Math.round(this.videoPlayer.volume * 100)}%`);
    }

    toggleMute() {
        if (!this.videoPlayer) return;
        this.videoPlayer.muted = !this.videoPlayer.muted;
        this.showToast(this.videoPlayer.muted ? 'Muted' : 'Unmuted');
    }

    showVideoControls() {
        const controls = document.getElementById('videoControls');
        if (!controls) return;
        controls.style.opacity = '1';
        controls.style.pointerEvents = 'auto';
        this.controlsVisible = true;
        this.startControlsAutoHide();
    }

    hideVideoControls() {
        if (!this.videoPlayer || this.videoPlayer.paused) return;
        const controls = document.getElementById('videoControls');
        if (!controls) return;
        controls.style.opacity = '0';
        controls.style.pointerEvents = 'none';
        this.controlsVisible = false;
        const speedMenu = document.querySelector('.speed-menu');
        if (speedMenu) speedMenu.style.display = 'none';
    }

    startControlsAutoHide() {
        this.stopControlsAutoHide();
        this.hideControlsTimeout = setTimeout(() => this.hideVideoControls(), 3000);
    }

    stopControlsAutoHide() {
        if (this.hideControlsTimeout) {
            clearTimeout(this.hideControlsTimeout);
            this.hideControlsTimeout = null;
        }
    }

    toggleSpeedMenu() {
        const menu = document.querySelector('.speed-menu');
        if (!menu) return;
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }

    updateVideoTimeDisplay() {
        const video = this.videoPlayer;
        if (!video) return;
        const timeDisplay = document.querySelector('.time-display');
        if (!timeDisplay) return;
        timeDisplay.textContent = `${this.formatVideoTime(video.currentTime)} / ${this.formatVideoTime(video.duration)}`;
    }

    formatVideoTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hrs > 0) return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    setupQuizEventDelegation() {
        const quizSection = document.getElementById('quizSection');
        if (!quizSection) return;
        if (this._quizClickHandler) quizSection.removeEventListener('click', this._quizClickHandler);
        this._quizClickHandler = (e) => {
            const button = e.target.closest('button');
            if (!button) return;
            switch (button.id) {
                case 'quizSubmitBtn': e.preventDefault(); this.handleQuizAnswerSubmit(); break;
                case 'quizSkipBtn': e.preventDefault(); this.handleQuizSkip(); break;
                case 'quizPrevBtn': e.preventDefault(); this.handleQuizPrevious(); break;
                case 'quizContinueAfterPassBtn': e.preventDefault(); this.handleQuizContinue(); break;
                case 'quizRetryFromResultBtn': case 'quizRetrySubmitBtn': e.preventDefault(); this.retryQuiz(); break;
            }
        };
        quizSection.addEventListener('click', this._quizClickHandler);
        if (this._quizKeydownHandler) quizSection.removeEventListener('keydown', this._quizKeydownHandler);
        this._quizKeydownHandler = (e) => { if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); this.handleQuizAnswerSubmit(); } };
        quizSection.addEventListener('keydown', this._quizKeydownHandler);
    }

    parseCompletionCriteria(lesson) {
        if (!lesson || !lesson.completion_criteria) return this.getDefaultCompletionCriteria(lesson ? lesson.type : null);
        const criteria = lesson.completion_criteria;
        return {
            criteriaType: criteria.criteria_type || 'manual',
            videoWatchPercentage: criteria.video_watch_percentage || 90,
            quizPassingScore: criteria.quiz_passing_score || 60,
            articleScrollPercentage: criteria.article_scroll_percentage || 90
        };
    }

    getDefaultCompletionCriteria(lessonType) {
        const defaults = {
            video: { criteriaType: 'watch_video', videoWatchPercentage: 90, quizPassingScore: null, articleScrollPercentage: null },
            quiz: { criteriaType: 'pass_quiz', videoWatchPercentage: null, quizPassingScore: 60, articleScrollPercentage: null },
            article: { criteriaType: 'read_article', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: 90 },
            assignment: { criteriaType: 'submit_assignment', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: null },
            file: { criteriaType: 'manual', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: null },
            live_session: { criteriaType: 'manual', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: null },
            coding_exercise: { criteriaType: 'manual', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: null }
        };
        return defaults[lessonType] || { criteriaType: 'manual', videoWatchPercentage: null, quizPassingScore: null, articleScrollPercentage: null };
    }

    canAutoComplete(lesson) {
        if (!lesson) return false;
        const criteria = this.parseCompletionCriteria(lesson);
        switch (criteria.criteriaType) {
            case 'watch_video':
                const actualWatchTime = this.calculateUniqueWatchTime();
                if (this.videoWatchPercentage >= 100) {
                    return true;
                }
                return this.videoWatchPercentage >= criteria.videoWatchPercentage &&
                       actualWatchTime >= this.videoCompletionMinWatchTime;
            case 'pass_quiz':
                return this.quizCompleted && this.quizResultData && this.quizResultData.passed;
            case 'read_article':
                return this.articleScrollPercentage >= criteria.articleScrollPercentage;
            case 'submit_assignment':
                return false;
            default:
                return false;
        }
    }

    getCompletionActionLabel(lesson) {
        if (!lesson) return 'Mark as Complete';
        const criteria = this.parseCompletionCriteria(lesson);
        switch (criteria.criteriaType) {
            case 'watch_video': return `Watch ${criteria.videoWatchPercentage}% to Complete`;
            case 'read_article': return `Read ${criteria.articleScrollPercentage}% to Complete`;
            case 'pass_quiz': return `Pass Quiz (${criteria.quizPassingScore}%)`;
            case 'submit_assignment': return 'Submit Assignment';
            default: return 'Mark as Complete';
        }
    }

    getQuestionTypeLabel(qt) {
        return { 'single_choice': 'Single Choice', 'multiple_choice': 'Multiple Choice', 'true_false': 'True / False', 'short_answer': 'Short Answer' }[qt] || 'Question';
    }

    getQuestionTypeIcon(qt) {
        return { 'single_choice': '<i class="fas fa-dot-circle"></i>', 'multiple_choice': '<i class="fas fa-check-square"></i>', 'true_false': '<i class="fas fa-toggle-on"></i>', 'short_answer': '<i class="fas fa-pen"></i>' }[qt] || '<i class="fas fa-question-circle"></i>';
    }

    getQuestionInstruction(qt) {
        return { 'single_choice': 'Select one correct answer', 'multiple_choice': 'Select all correct answers', 'true_false': 'Select True or False', 'short_answer': 'Type your answer below' }[qt] || 'Answer the question';
    }

    setupVideoTracking() {
        this.stopVideoTracking();
        this.videoAutoCompleted = false;

        if (!this.videoResumeTimestamp || this.videoResumeTimestamp <= 0) {
            this.watchedSegments = [];
            this.videoWatchPercentage = 0;
        } else {
            this.currentSegmentStart = this.videoResumeTimestamp;
            this.lastVideoTimeUpdate = this.videoResumeTimestamp;

            if (this.watchedSegments.length === 0) {
                this.initializeWatchedSegmentsFromResume(this.videoResumeTimestamp);
            }

            const duration = this.videoPlayer?.duration || 0;
            if (duration > 0) {
                this.videoWatchPercentage = Math.round((this.videoResumeTimestamp / duration) * 100);
            }
        }

        this.videoMetadataLoaded = false;
        this.videoResumeApplied = false;

        const lesson = this.getCurrentLesson();
        if (!lesson || lesson.type !== 'video') return;

        const videoElement = this.videoPlayer;
        if (!videoElement) return;

        const criteria = this.parseCompletionCriteria(lesson);
        this.videoCompletionThreshold = criteria.videoWatchPercentage || 90;

        videoElement.addEventListener('timeupdate', this.handleVideoTimeUpdate);
        videoElement.addEventListener('ended', this.handleVideoEnded);
        videoElement.addEventListener('play', this.handleVideoPlay);
        videoElement.addEventListener('pause', this.handleVideoPause);

        this.videoTrackingInterval = setInterval(() => this.checkVideoProgress(videoElement), 2000);

        this.updateCompleteButtonLabel();
        this.updateVideoCompletionIndicator();
    }

    initializeWatchedSegmentsFromResume(timestamp) {
        if (!timestamp || timestamp <= 0) return;

        this.watchedSegments = [{
            start: 0,
            end: timestamp
        }];

        this.currentSegmentStart = timestamp;
        this.lastVideoTimeUpdate = timestamp;


    }

    handleVideoTimeUpdate = () => {
        if (this.videoPlayer) {
            const currentTime = this.videoPlayer.currentTime;

            if (!this.isSeeking && this.lastVideoTimeUpdate > 0) {
                const timeDiff = Math.abs(currentTime - this.lastVideoTimeUpdate);
                if (timeDiff > this.seekThreshold) {
                    this.handleVideoSeek(this.lastVideoTimeUpdate, currentTime);
                }
            }

            this.lastVideoTimeUpdate = currentTime;
            this.updateVideoCompletionIndicator();

            const now = Date.now();
            if (now - this.lastSaveTime >= this.saveInterval && !this.isSavingVideo) {
                this.saveVideoProgress();
                this.lastSaveTime = now;
            }
        }
    };

    handleVideoPlay = () => {
        if (!this.isSeeking && this.videoPlayer) {
            this.currentSegmentStart = this.videoPlayer.currentTime;
        }
    };

    handleVideoPause = () => {
        this.endCurrentWatchSegment();
    };

    handleVideoSeek(fromTime, toTime) {
        if (this.videoPlayer && !this.videoPlayer.paused) {
            this.endCurrentWatchSegment();
            this.currentSegmentStart = toTime;
        }
    }

    handleVideoSeekComplete() {
        if (this.videoPlayer && !this.videoPlayer.paused) {
            this.currentSegmentStart = this.videoPlayer.currentTime;
        }
    }

    endCurrentWatchSegment() {
        if (this.videoPlayer && this.currentSegmentStart > 0 && !this.isSeeking) {
            const endTime = this.videoPlayer.currentTime;
            if (endTime > this.currentSegmentStart) {
                this.addWatchedSegment(this.currentSegmentStart, endTime);
            }
            this.currentSegmentStart = 0;
        }
    }

    addWatchedSegment(start, end) {
        if (start >= end || start < 0 || end <= 0) return;

        let merged = false;
        for (let i = 0; i < this.watchedSegments.length; i++) {
            const seg = this.watchedSegments[i];

            if (start <= seg.end && end >= seg.start) {
                seg.start = Math.min(seg.start, start);
                seg.end = Math.max(seg.end, end);
                merged = true;
                break;
            }
        }

        if (!merged) {
            this.watchedSegments.push({ start, end });
        }

        this.watchedSegments.sort((a, b) => a.start - b.start);

        if (this.watchedSegments.length > this.maxWatchedSegments) {
            this.mergeOldSegments();
        }
    }

    mergeOldSegments() {
        if (this.watchedSegments.length <= 1) return;

        const first = this.watchedSegments[0];
        const second = this.watchedSegments[1];

        first.end = Math.max(first.end, second.end);
        this.watchedSegments.splice(1, 1);
    }

    calculateUniqueWatchTime() {
        let totalTime = 0;
        for (const seg of this.watchedSegments) {
            totalTime += (seg.end - seg.start);
        }
        return totalTime;
    }

    async applyVideoResumePoint() {
        if (this.videoResumeApplied || !this.videoPlayer || !this.videoMetadataLoaded) return;

        const resumeTime = this.videoResumeTimestamp;
        if (resumeTime > 0) {
            try {
                if (!this.videoPlayer.duration) {
                    await this.waitForVideoMetadata();
                }

                const duration = this.videoPlayer.duration;
                if (duration > 0) {
                    this.videoWatchPercentage = Math.round((resumeTime / duration) * 100);

                    if (this.watchedSegments.length === 0) {
                        this.initializeWatchedSegmentsFromResume(resumeTime);
                    }

                    this.updateVideoCompletionIndicator();
                }

                if (resumeTime < this.videoPlayer.duration - 5) {
                    this.videoPlayer.currentTime = resumeTime;
                    this.lastVideoTimeUpdate = resumeTime;
                    this.currentSegmentStart = resumeTime;

                    this.showVideoResumeIndicator(resumeTime);
                }
            } catch (e) {
                console.warn('Failed to apply resume point:', e);
            }
        }

        this.videoResumeApplied = true;
    }

    waitForVideoMetadata() {
        if (this.videoPlayer.duration) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Timeout waiting for video metadata'));
            }, 10000);

            const checkMetadata = () => {
                if (this.videoPlayer.duration) {
                    clearTimeout(timeout);
                    resolve();
                } else if (this.videoPlayer.readyState >= 2) {
                    clearTimeout(timeout);
                    resolve();
                } else {
                    setTimeout(checkMetadata, 100);
                }
            };

            checkMetadata();
        });
    }

    showVideoResumeIndicator(timestamp) {
        const resumeIndicator = document.createElement('div');
        resumeIndicator.className = 'video-resume-indicator';
        resumeIndicator.style.cssText = 'position:absolute;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(139,92,246,0.9);color:#FFF;padding:8px 16px;border-radius:20px;font-size:0.85rem;z-index:100;animation:fadeInOut 3s forwards;';
        resumeIndicator.textContent = `Resumed from ${this.formatVideoTime(timestamp)}`;

        const videoContainer = document.getElementById('videoContainer');
        if (videoContainer) {
            videoContainer.appendChild(resumeIndicator);
            setTimeout(() => {
                if (resumeIndicator.parentNode) {
                    resumeIndicator.parentNode.removeChild(resumeIndicator);
                }
            }, 3000);
        }

        if (!document.getElementById('videoResumeAnimation')) {
            const style = document.createElement('style');
            style.id = 'videoResumeAnimation';
            style.textContent = '@keyframes fadeInOut{0%{opacity:0;}10%{opacity:1;}80%{opacity:1;}100%{opacity:0;}}';
            document.head.appendChild(style);
        }
    }

    handleVideoEnded = () => {
        this.videoWatchPercentage = 100;
        this.endCurrentWatchSegment();

        if (this.videoPlayer && this.videoPlayer.duration) {
            this.addWatchedSegment(0, this.videoPlayer.duration);
        }

        const lesson = this.getCurrentLesson();
        if (lesson && this.canAutoComplete(lesson)) {
            this.markLessonComplete(true);
        }
        this.updateVideoCompletionIndicator();
    };

    checkVideoProgress(videoElement) {
        if (!videoElement || videoElement.duration === 0 || this.videoAutoCompleted) return;

        const currentTime = videoElement.currentTime;
        const duration = videoElement.duration;

        const effectiveWatchTime = Math.max(currentTime, this.videoResumeTimestamp);
        this.videoWatchPercentage = Math.round((effectiveWatchTime / duration) * 100);

        const uniqueWatchTime = this.calculateUniqueWatchTime();
        const minWatchTimeMet = uniqueWatchTime >= this.videoCompletionMinWatchTime;

        if (this.videoWatchPercentage >= 100) {
            this.videoAutoCompleted = true;
            const lesson = this.getCurrentLesson();
            if (lesson && this.canAutoComplete(lesson)) {
                this.markLessonComplete(true);
                this.showToast(`🎉 Video fully watched - Lesson auto-completed!`);
            }
            this.updateVideoCompletionIndicator();
            return;
        }

        if (this.videoWatchPercentage >= this.videoCompletionThreshold && minWatchTimeMet) {
            this.videoAutoCompleted = true;
            const lesson = this.getCurrentLesson();
            if (lesson && this.canAutoComplete(lesson)) {
                this.markLessonComplete(true);
                this.showToast(`🎉 Watched ${this.videoCompletionThreshold}% - Lesson auto-completed!`);
            }
        } else if (this.videoWatchPercentage >= this.videoCompletionThreshold && !minWatchTimeMet) {
            const remainingTime = Math.ceil(this.videoCompletionMinWatchTime - uniqueWatchTime);
            this.updateVideoCompletionIndicator(`Need ${remainingTime} more seconds of actual watch time`);
        }
    }

    updateVideoCompletionIndicator(customMessage) {
        const indicator = document.getElementById('videoCompletionIndicator');
        if (!indicator) return;

        const uniqueWatchTime = this.calculateUniqueWatchTime();
        const minWatchTimeMet = uniqueWatchTime >= this.videoCompletionMinWatchTime;

        if (customMessage) {
            indicator.innerHTML = `<span style="font-size:0.75rem;color:#F59E0B;">⚠️ ${customMessage}</span>`;
        } else if (this.videoWatchPercentage >= 100) {
            indicator.innerHTML = `
                <span style="font-size:0.75rem;color:#10B981;">
                    ✅ Video fully watched
                    ${this.videoAutoCompleted ? ' - Completed!' : ''}
                </span>
            `;
        } else {
            indicator.innerHTML = `
                <span style="font-size:0.75rem;color:#888;">
                    📊 ${this.videoWatchPercentage}% watched (${this.videoCompletionThreshold}% needed)
                    ${!minWatchTimeMet && this.videoWatchPercentage >= this.videoCompletionThreshold ?
                        ` | ⏱️ ${Math.ceil(this.videoCompletionMinWatchTime - uniqueWatchTime)}s more needed` : ''}
                    ${this.videoAutoCompleted ? ' ✅' : ''}
                </span>
            `;
        }
    }

    stopVideoTracking() {
        if (this.videoPlayer) {
            this.videoPlayer.removeEventListener('timeupdate', this.handleVideoTimeUpdate);
            this.videoPlayer.removeEventListener('ended', this.handleVideoEnded);
            this.videoPlayer.removeEventListener('play', this.handleVideoPlay);
            this.videoPlayer.removeEventListener('pause', this.handleVideoPause);
        }
        if (this.videoTrackingInterval) {
            clearInterval(this.videoTrackingInterval);
            this.videoTrackingInterval = null;
        }

        this.endCurrentWatchSegment();
    }

    saveVideoProgress() {
        const lesson = this.getCurrentLesson();
        if (this.videoPlayer && lesson && lesson.type === 'video') {
            const currentTime = Math.floor(this.videoPlayer.currentTime);
            if (currentTime > 0 && currentTime !== this.lastSaveTime) {
                this.lastSaveTime = currentTime;

                this.videoSaveQueue.push({
                    enrollmentId: this.enrollmentId,
                    lessonId: lesson.id,
                    timestamp: currentTime
                });

                this.processVideoSaveQueue();
            }
        }
    }

    saveVideoProgressImmediate() {
        const lesson = this.getCurrentLesson();
        if (this.videoPlayer && lesson && lesson.type === 'video') {
            const currentTime = Math.floor(this.videoPlayer.currentTime);
            if (currentTime > 0) {
                ApiService.saveVideoResumePoint(this.enrollmentId, lesson.id, currentTime)
                    .then(result => {
                        if (result.success) {
                            console.log('Video resume point saved');
                        }
                    })
                    .catch(err => console.error('Failed to save video resume point:', err));
            }
        }
    }

    async processVideoSaveQueue() {
        if (this.isSavingVideo || this.videoSaveQueue.length === 0) return;

        this.isSavingVideo = true;

        try {
            const latestSave = this.videoSaveQueue.pop();
            this.videoSaveQueue = [];

            const result = await ApiService.saveVideoResumePoint(
                latestSave.enrollmentId,
                latestSave.lessonId,
                latestSave.timestamp
            );

            if (result.success) {
                console.log('Video resume point saved to backend');
            }
        } catch (e) {
            console.error('Failed to save video resume point:', e);
        } finally {
            this.isSavingVideo = false;

            if (this.videoSaveQueue.length > 0) {
                setTimeout(() => this.processVideoSaveQueue(), 1000);
            }
        }
    }

    async loadVideoResumePoint(enrollmentId, lessonId) {
        if (this.videoResumeLoading) return this.videoResumeTimestamp;

        this.videoResumeLoading = true;

        try {
            const result = await ApiService.getVideoResumePoint(enrollmentId, lessonId);

            if (result && result.success && result.timestamp > 0) {
                this.videoResumeTimestamp = result.timestamp;
                this.videoResumeLoaded = true;
                return result.timestamp;
            }
        } catch (e) {
            console.warn('Failed to load video resume point:', e);
        } finally {
            this.videoResumeLoading = false;
        }

        return 0;
    }

    setupArticleScrollTracking() {
        this.stopArticleScrollTracking();
        this.articleAutoCompleted = false;
        this.articleScrollPercentage = 0;
        this.articleCompletionInProgress = false;

        const lesson = this.getCurrentLesson();
        if (!lesson || lesson.type !== 'article') return;

        this.articleContentElement = document.getElementById('articleBody');
        if (!this.articleContentElement) return;
        const criteria = this.parseCompletionCriteria(lesson);
        this.articleScrollThreshold = criteria.articleScrollPercentage || 90;

        const completedLessons = this.progressData?.completedLessons || [];
        if (completedLessons.includes(lesson.id)) {
            this.articleAutoCompleted = true;
            this.articleScrollPercentage = 100;
            this.updateArticleCompletionIndicator();
            return;
        }

        this.articleScrollTrackingActive = true;

        setTimeout(() => {
            this.checkArticleScrollProgress();
            this.updateArticleCompletionIndicator();
        }, 300);

        const scrollContainer = document.getElementById('articleSection');
        if (scrollContainer) {
            scrollContainer.addEventListener('scroll', this.handleArticleScroll);
        }
        window.addEventListener('scroll', this.handleArticleScroll);

        this.updateArticleCompletionIndicator();
        this.updateCompleteButtonLabel();
    }

    handleArticleScroll = () => {
        if (!this.articleScrollTrackingActive || this.articleAutoCompleted || this.articleCompletionInProgress) return;
        this.checkArticleScrollProgress();
        this.updateArticleCompletionIndicator();
    }

    checkArticleScrollProgress() {
        if (this.articleAutoCompleted || this.articleCompletionInProgress) return;

        const articleBody = document.getElementById('articleBody');
        if (!articleBody) return;

        const articleSection = document.getElementById('articleSection');
        const windowHeight = window.innerHeight;
        const articleHeight = articleBody.scrollHeight;

        if (articleHeight <= windowHeight) {
            this.articleScrollPercentage = 100;

            if (this.articleScrollPercentage >= this.articleScrollThreshold && !this.articleAutoCompleted && !this.articleCompletionInProgress) {
                const lesson = this.getCurrentLesson();
                if (lesson) {
                    const completedLessons = this.progressData?.completedLessons || [];
                    if (!completedLessons.includes(lesson.id)) {
                        this.articleAutoCompleted = true;
                        this.articleCompletionInProgress = true;
                        if (this.canAutoComplete(lesson)) {
                            this.markLessonComplete(true);
                            this.showToast(`📖 Article fully read - Lesson auto-completed!`);
                        }
                        setTimeout(() => {
                            this.articleCompletionInProgress = false;
                        }, 2000);
                    }
                }
            }
            return;
        }

        let scrollTop, elementTop, containerHeight;

        if (articleSection && articleSection.scrollHeight > articleSection.clientHeight) {
            containerHeight = articleSection.clientHeight;
            scrollTop = articleSection.scrollTop;
            const containerRect = articleSection.getBoundingClientRect();
            const articleRect = articleBody.getBoundingClientRect();
            elementTop = articleRect.top - containerRect.top + articleSection.scrollTop;
        } else {
            containerHeight = windowHeight;
            scrollTop = window.scrollY;
            elementTop = articleBody.getBoundingClientRect().top + window.scrollY;
        }

        const scrollBottom = scrollTop + containerHeight;
        const elementBottom = elementTop + articleHeight;

        if (elementBottom <= scrollTop || elementTop >= scrollBottom) {
            this.articleScrollPercentage = 0;
            return;
        }

        const scrolledPastTop = scrollBottom - elementTop;
        const percentage = Math.min(100, Math.max(0, Math.round((scrolledPastTop / articleHeight) * 100)));

        this.articleScrollPercentage = percentage;

        if (this.articleScrollPercentage >= this.articleScrollThreshold && !this.articleAutoCompleted && !this.articleCompletionInProgress) {
            const lesson = this.getCurrentLesson();
            if (lesson) {
                const completedLessons = this.progressData?.completedLessons || [];
                if (!completedLessons.includes(lesson.id)) {
                    this.articleAutoCompleted = true;
                    this.articleCompletionInProgress = true;
                    if (this.canAutoComplete(lesson)) {
                        this.markLessonComplete(true);
                        this.showToast(`📖 Read ${this.articleScrollThreshold}% - Lesson auto-completed!`);
                    }
                    setTimeout(() => {
                        this.articleCompletionInProgress = false;
                    }, 2000);
                }
            }
        }
    }

    updateArticleCompletionIndicator() {
        let indicator = document.getElementById('articleCompletionIndicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'articleCompletionIndicator';
            indicator.style.cssText = 'text-align:center;padding:4px 16px;background:rgba(0,0,0,0.3);border-radius:0 0 8px 8px;margin-top:0;';
            const articleSection = document.getElementById('articleSection');
            if (articleSection) {
                const articleBody = document.getElementById('articleBody');
                if (articleBody) {
                    articleBody.parentNode.insertBefore(indicator, articleBody.nextSibling);
                } else {
                    articleSection.appendChild(indicator);
                }
            }
        }

        const percentage = this.articleScrollPercentage;
        const threshold = this.articleScrollThreshold;
        const isShortArticle = this.articleContentElement && this.articleContentElement.scrollHeight <= window.innerHeight;

        indicator.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;">
                <span style="font-size:0.75rem;color:#888;">
                    ${isShortArticle && percentage >= 100 ? '📖 Article fully visible' : `📖 ${percentage}% read (${threshold}% needed)`}
                    ${this.articleAutoCompleted ? ' ✅' : ''}
                </span>
                <div style="width:120px;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;">
                    <div style="height:100%;background:#10B981;border-radius:2px;width:${Math.min(100, (percentage / threshold) * 100)}%;transition:width 0.3s ease;"></div>
                </div>
            </div>
        `;
    }

    stopArticleScrollTracking() {
        this.articleScrollTrackingActive = false;
        this.articleCompletionInProgress = false;
        const scrollContainer = document.getElementById('articleSection');
        if (scrollContainer) scrollContainer.removeEventListener('scroll', this.handleArticleScroll);
        window.removeEventListener('scroll', this.handleArticleScroll);
        this.articleContentElement = null;
    }

    async loadCourseStructure() {
        const data = await this.fetchCourseStructure();
        this.courseData = data;
        if (!this.courseId && data.courseId) this.courseId = data.courseId;
        if (!this.courseId) this.courseId = this.getCourseIdFromUrl() || 'python-data-science';
        const navTitle = document.getElementById('navCourseTitle');
        if (navTitle && data.courseTitle) navTitle.textContent = data.courseTitle;
    }

    async fetchCourseStructure() {
        const data = await ApiService.getEnrollmentCurriculum(this.enrollmentId);
        return this.processCourseStructure(data);
    }

    processCourseStructure(apiData) {
        if (!apiData || !apiData.sections) return apiData;
        if (apiData.sections && Array.isArray(apiData.sections)) {
            apiData.sections = apiData.sections.map(section => ({ ...section, lessons: (section.lessons || []).map(lesson => this.normalizeLessonData(lesson)) }));
        }
        return apiData;
    }

    normalizeLessonData(lesson) {
        return {
            id: lesson.id, title: lesson.title, type: lesson.type,
            duration: lesson.duration || this.getDurationString(lesson.duration_seconds),
            durationSeconds: lesson.duration_seconds || 0, order: lesson.order,
            preview: lesson.preview || false, hasResources: lesson.has_resources || false,
            completion_criteria: lesson.completion_criteria || null,
            description: lesson.description || '',
            file_url: lesson.file_url || null, file_name: lesson.file_name || null,
            quizData: lesson.quizData || null,
            assignmentData: lesson.assignmentData || null,
            resources: lesson.resources || [],
            transcript: lesson.transcript || null,
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

    async fetchLessonContent(lessonId) {
        const data = await ApiService.getLessonContent(this.enrollmentId, lessonId);

        if (data && data.type === 'video') {
            const resumeTimestamp = await this.loadVideoResumePoint(this.enrollmentId, lessonId);
            if (resumeTimestamp > 0) {
                this.videoResumeTimestamp = resumeTimestamp;
                data.video_progress = { timestamp: resumeTimestamp };
                this.initializeWatchedSegmentsFromResume(resumeTimestamp);
            }
        } else if (data && data.video_progress) {
            this.videoResumeTimestamp = data.video_progress.timestamp || 0;
            if (this.videoResumeTimestamp > 0) {
                this.initializeWatchedSegmentsFromResume(this.videoResumeTimestamp);
            }
        }

        return data;
    }

    showContentLoading() {
        ['videoPlayerSection','articleSection','quizSection','assignmentSection','fileSection'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
        const articleSection = document.getElementById('articleSection');
        if (articleSection) {
            articleSection.style.display = '';
            const body = document.getElementById('articleBody');
            if (body) body.innerHTML = `<div style="text-align:center;padding:60px;"><div style="display:inline-block;width:40px;height:40px;border:3px solid #2A2A3E;border-top-color:#8B5CF6;border-radius:50%;animation:spin 0.8s linear infinite;"></div><p style="color:#888;margin-top:16px;">Loading...</p></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>`;
        }
    }

    async loadProgressData() {
        try {
            this.progressData = await ApiService.getEnrollmentProgress(this.enrollmentId);
        } catch(e) {
            this.progressData = this.getDefaultProgressData();
        }
        this.restoreState();
    }

    getDefaultProgressData() {
        return {
            enrollmentId: this.enrollmentId,
            overallProgress: 0,
            completedLessons: [],
            completedCount: 0,
            totalLessons: this.getAllLessons().length || 12,
            bookmarkedLessons: []
        };
    }

    restoreState() {
        if (!this.progressData) return;
        if (this.progressData.bookmarkedLessons) {
            this.progressData.bookmarkedLessons.forEach(id => this.bookmarkedLessons.add(id));
        }
        this.updateProgressUI();
        this.updateBookmarkUI();
    }

    checkCourseCompletion() {
        if (!this.progressData || !this.courseData) return false;
        const totalLessons = this.courseData.totalLessons || this.getAllLessons().length;
        const completedCount = this.progressData.completedCount ||
                              (this.progressData.completedLessons?.length || 0);

        return totalLessons > 0 && completedCount >= totalLessons;
    }

    async determineStartingLesson() {
        let targetId = this.getLessonIdFromUrl();
        const all = this.getAllLessons();
        if (!all.length) return;
        if (targetId && !all.some(l => l.id === targetId)) targetId = null;
        if (!targetId && all.length) targetId = all[0].id;
        if (targetId) await this.navigateToLessonById(targetId, true);
    }

    renderSidebar() {
        const sc = document.getElementById('sidebarCurriculum');
        if (!sc) return;
        if (!this.courseData?.sections) { sc.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">Loading...</p>'; return; }
        let html = '';
        this.courseData.sections.forEach((s, si) => {
            const cl = this.progressData?.completedLessons||[];
            html += `<div class="curriculum-section"><div class="curriculum-section-header" onclick="toggleSection(this)"><div class="section-header-left"><i class="fas fa-chevron-down section-chevron"></i><span class="section-number">Section ${si+1}</span></div><div class="section-header-right"><span class="section-title-text">${this.escapeHtml(s.title)}</span><span class="section-progress">${s.lessons.filter(l=>cl.includes(l.id)).length}/${s.lessons.length}</span></div></div><div class="curriculum-lessons" style="display:block;">${s.lessons.map(l => {
                const isDone = cl.includes(l.id); const isBm = this.bookmarkedLessons.has(l.id); const isAct = l.id === this.currentLessonId;
                return `<div class="curriculum-lesson-item ${isDone?'completed':''} ${isAct?'active':''}" data-lesson="${l.id}" onclick="navigateToLesson(${l.id})"><div class="lesson-item-left"><span class="lesson-status-icon ${isDone?'completed':''}">${isDone?'<i class="fas fa-check-circle"></i>':'<span class="status-circle"></span>'}</span><span class="lesson-item-title">${this.escapeHtml(l.title)}</span></div><div class="lesson-item-right"><span class="lesson-item-type ${l.type}">${this.getTypeIcon(l.type)}</span><span class="lesson-item-duration">${l.duration}</span>${isBm?'<i class="fas fa-bookmark" style="color:#F59E0B;font-size:0.7rem;margin-left:4px;"></i>':''}</div></div>`;
            }).join('')}</div></div>`;
        });

        if (this.checkCourseCompletion()) {
            this.courseCompleted = true;
            html += this.renderCertificateSection();
        }

        sc.innerHTML = html;
        if (this.currentLessonId) this.updateSidebarActive();
    }

    renderCertificateSection() {
        return `
            <div class="curriculum-section certificate-section" style="margin-top:16px;border-top:2px solid rgba(139,92,246,0.3);padding-top:16px;">
                <div class="curriculum-section-header" style="background:rgba(139,92,246,0.1);border-radius:8px;cursor:pointer;" onclick="toggleCertificateSection(this)">
                    <div class="section-header-left">
                        <i class="fas fa-chevron-down section-chevron" style="color:#F59E0B;"></i>
                        <span class="section-number" style="color:#F59E0B;">🎓</span>
                    </div>
                    <div class="section-header-right">
                        <span class="section-title-text" style="color:#F59E0B;font-weight:600;">Certificate</span>
                        <span class="section-progress" style="color:#10B981;">✓ Earned</span>
                    </div>
                </div>
                <div class="curriculum-certificate-content" style="display:block;padding:16px;">
                    <div class="certificate-card" onclick="showCertificate()" style="background:linear-gradient(135deg,rgba(139,92,246,0.15) 0%,rgba(16,185,129,0.1) 100%);border:1px solid rgba(139,92,246,0.3);border-radius:12px;padding:20px;text-align:center;cursor:pointer;transition:all 0.3s ease;" onmouseover="this.style.transform='scale(1.02)';this.style.boxShadow='0 8px 24px rgba(139,92,246,0.2)';" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='none';">
                        <div style="font-size:3rem;margin-bottom:12px;">
                            <i class="fas fa-trophy" style="color:#F59E0B;"></i>
                        </div>
                        <h4 style="color:#F59E0B;margin-bottom:8px;font-size:1.1rem;font-weight:600;">Congratulations!</h4>
                        <p style="color:#AAA;font-size:0.85rem;margin-bottom:12px;">You have completed this course</p>
                        <div style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:rgba(139,92,246,0.2);color:#A78BFA;border-radius:6px;font-size:0.85rem;font-weight:500;">
                            <i class="fas fa-certificate"></i> View Certificate
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showCertificateModal() {
        const existingModal = document.getElementById('certificateModal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.id = 'certificateModal';
        modal.style.cssText = 'display:flex;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:10001;overflow:auto;align-items:center;justify-content:center;padding:20px;';

        const courseTitle = this.courseData?.courseTitle || 'Course';

        modal.innerHTML = `
            <div style="max-width:800px;width:100%;background:linear-gradient(135deg,#1F2937 0%,#111827 100%);border:2px solid rgba(139,92,246,0.3);border-radius:16px;padding:40px;text-align:center;position:relative;overflow:hidden;">
                <button onclick="closeCertificateModal()" style="position:absolute;top:16px;right:16px;background:rgba(255,255,255,0.1);border:none;color:#FFF;width:36px;height:36px;border-radius:50%;cursor:pointer;font-size:1.2rem;display:flex;align-items:center;justify-content:center;">
                    <i class="fas fa-times"></i>
                </button>

                <div style="position:absolute;top:-50px;left:-50px;width:150px;height:150px;background:rgba(139,92,246,0.1);border-radius:50%;"></div>
                <div style="position:absolute;bottom:-50px;right:-50px;width:150px;height:150px;background:rgba(139,92,246,0.1);border-radius:50%;"></div>

                <div style="position:relative;z-index:1;">
                    <div style="margin-bottom:20px;">
                        <i class="fas fa-trophy" style="font-size:4rem;color:#F59E0B;"></i>
                    </div>
                    <h2 style="color:#F59E0B;font-size:1.8rem;margin-bottom:8px;font-weight:700;">CONGRATULATIONS!</h2>
                    <p style="color:#FFF;font-size:1.2rem;margin-bottom:24px;">You have successfully completed the course</p>

                    <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);border-radius:12px;padding:20px;margin-bottom:24px;">
                        <h3 style="color:#A78BFA;font-size:1.5rem;margin-bottom:8px;">${this.escapeHtml(courseTitle)}</h3>
                    </div>

                    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
                        <a href="/dashboard/certificates"
                           style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.3);border-radius:8px;text-decoration:none;font-weight:600;">
                            <i class="fas fa-external-link-alt"></i> Go to Dashboard > Certificates
                        </a>
                    </div>
                    <p style="color:#888;font-size:0.85rem;margin-top:16px;">
                        You can visit and download your certificate in the Certificates section of your dashboard.
                    </p>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCertificateModal();
            }
        });
    }

    async navigateToLessonById(lessonId, isInit=false) {
        this.saveVideoProgressImmediate();

        this.stopVideoTracking();
        this.stopArticleScrollTracking();
        this.resetQuizState();
        this.resetAssignmentState();

        const oldLessonId = this.currentLessonId;

        this.videoResumeTimestamp = 0;
        this.videoMetadataLoaded = false;
        this.videoResumeApplied = false;

        if (oldLessonId !== lessonId) {
            this.watchedSegments = [];
            this.currentSegmentStart = 0;
            this.lastVideoTimeUpdate = 0;
            this.videoWatchPercentage = 0;
        }

        let found = false;
        for (let si=0; si<this.courseData.sections.length; si++) {
            const sec = this.courseData.sections[si];
            for (let li=0; li<sec.lessons.length; li++) {
                if (sec.lessons[li].id === lessonId) {
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
            const lesson = this.courseData.sections[this.currentSectionIndex].lessons[this.currentLessonIndex];

            if (lesson) {
                const content = await this.fetchLessonContent(lessonId);

                if (content) {
                    this.courseData.sections[this.currentSectionIndex].lessons[this.currentLessonIndex] = {
                        ...lesson,
                        ...content,
                        id: lesson.id,
                        type: lesson.type,
                        completion_criteria: lesson.completion_criteria || content.completion_criteria,
                        description: content.description || lesson.description || '',
                        resources: content.resources || lesson.resources || [],
                        transcript: content.transcript || lesson.transcript || null
                    };
                }
            }

            const updatedLesson = this.courseData.sections[this.currentSectionIndex].lessons[this.currentLessonIndex];

            if (updatedLesson?.type === 'quiz' && updatedLesson.quizData) {
                this.prepareQuizQuestions(updatedLesson);
                await this.loadQuizAttemptStatus(lessonId);
            }
            if (updatedLesson?.type === 'assignment' && updatedLesson.assignmentData) {
                await this.loadAssignmentDetails(lessonId);
            }

            this.renderLesson();
            this.updateSidebarActive();
            this.scrollToActiveLesson();
            this.setupVideoTracking();
            this.setupArticleScrollTracking();
        }
    }

    async loadQuizAttemptStatus(lessonId) {
        try {
            const status = await ApiService.getQuizAttemptStatus(this.enrollmentId, lessonId);
            if (status && status.success) {
                this.quizAttemptsUsed = status.attempts_used || 0;
                this.maxQuizAttempts = status.max_attempts || 3;
                this.quizAttemptsRemaining = status.attempts_remaining || 0;
                this.quizBestScore = status.best_score || 0;
                this.quizCanAttempt = status.can_attempt !== undefined ? status.can_attempt : (this.quizAttemptsUsed < this.maxQuizAttempts);
            }
        } catch (e) {
            console.warn('Failed to load quiz attempt status:', e);
            this.quizCanAttempt = true;
        }
    }

    async loadAssignmentDetails(lessonId) {
        try {
            const details = await ApiService.getAssignmentDetails(this.enrollmentId, lessonId);
            if (details && details.success) {
                this.assignmentData = details.assignment;
                this.assignmentSubmissions = details.submissions || [];
            }
        } catch (e) {
            console.warn('Failed to load assignment details:', e);
        }
    }

    resetAssignmentState() {
        this.assignmentData = null;
        this.assignmentSubmissions = [];
        this.selectedFiles = [];
        this.isAssignmentSubmitting = false;
    }

    async navigateLesson(dir) {
        const all = this.getAllLessons();
        const idx = all.findIndex(l => l.id === this.currentLessonId) + dir;
        if (idx >= 0 && idx < all.length) await this.navigateToLessonById(all[idx].id);
    }

    getAllLessons() {
        let all = [];
        (this.courseData?.sections||[]).forEach(s => {
            if (s.lessons) all = all.concat(s.lessons);
        });
        return all;
    }

    getCurrentLesson() {
        const s = this.courseData?.sections?.[this.currentSectionIndex];
        return s?.lessons?.[this.currentLessonIndex] || null;
    }

    scrollToActiveLesson() {
        setTimeout(() => {
            const el = document.querySelector('.curriculum-lesson-item.active');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    renderLesson() {
        const lesson = this.getCurrentLesson();
        if (!lesson) return;
        this.currentLessonType = lesson.type;
        ['videoPlayerSection','articleSection','quizSection','assignmentSection','fileSection'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });

        this.updateTranscriptTabVisibility(lesson.type === 'video');

        const resources = lesson.resources || [];
        this.updateResourcesTabBadge(resources.length);

        this.renderOverviewContent(lesson);

        switch(lesson.type) {
            case 'video':
                const vs = document.getElementById('videoPlayerSection'); if (vs) vs.style.display = '';
                const videoTitle = document.getElementById('videoLessonTitle'); if (videoTitle) videoTitle.textContent = lesson.title;
                if (this.videoPlayer && lesson.videoUrl) {
                    this.videoPlayer.src = lesson.videoUrl;
                    this.videoPlayer.load();

                    this.videoMetadataLoaded = false;
                    this.videoResumeApplied = false;
                }
                const desc = document.getElementById('videoDescription'); if (desc && lesson.description) desc.innerHTML = `<p style="color:#AAA;padding:16px;">${this.escapeHtml(lesson.description)}</p>`;
                const ph = document.getElementById('videoPlaceholder'); if (ph) ph.style.display = (this.videoPlayer && lesson.videoUrl) ? 'none' : '';
                let indicator = document.getElementById('videoCompletionIndicator');
                if (!indicator) { indicator = document.createElement('div'); indicator.id = 'videoCompletionIndicator'; indicator.style.cssText = 'text-align:center;padding:4px;background:rgba(0,0,0,0.3);'; const vsEl = document.getElementById('videoPlayerSection'); if (vsEl) vsEl.appendChild(indicator); }
                this.updateVideoCompletionIndicator();
                const ov = document.getElementById('videoOverlay'); if (ov) { ov.style.display = ''; ov.classList.remove('playing'); }
                const bp = document.getElementById('videoBigPlayBtn'); if (bp) { bp.innerHTML = '<i class="fas fa-play"></i>'; bp.style.opacity = '1'; bp.style.pointerEvents = 'auto'; }

                this.renderTranscriptContent(lesson);
                break;
            case 'article':
                const as = document.getElementById('articleSection'); if (as) as.style.display = '';
                document.getElementById('articleTitle').textContent = lesson.title;
                document.getElementById('articleBody').innerHTML = lesson.articleContent || '<p>Loading...</p>';
                const oldIndicator = document.getElementById('articleCompletionIndicator'); if (oldIndicator) oldIndicator.remove();
                setTimeout(() => this.setupArticleScrollTracking(), 200);
                break;
            case 'quiz':
                const qs = document.getElementById('quizSection'); if (qs) { qs.style.display = ''; this.buildQuizUI(); }
                break;
            case 'assignment':
                const asg = document.getElementById('assignmentSection'); if (asg) { asg.style.display = ''; this.buildAssignmentUI(); }
                break;
            case 'file':
                const fs = document.getElementById('articleSection'); if (fs) fs.style.display = '';
                document.getElementById('articleTitle').textContent = lesson.title;
                const fileUrl = lesson.fileUrl || lesson.file_url; const fileName = lesson.fileName || lesson.file_name || 'File';
                const displayName = this.getDisplayFileName(fileUrl, fileName); const fileType = fileUrl ? this.getFileType(fileUrl, fileName) : 'other';
                const extension = fileUrl ? this.getFileExtension(fileUrl, fileName) : '';
                document.getElementById('articleBody').innerHTML = fileUrl ? `<div style="text-align:center;padding:40px 20px;"><div style="font-size:4rem;color:${this.getFileIconColor(fileType)};display:block;margin-bottom:16px;"><i class="fas ${this.getFileTypeIcon(fileType)}"></i></div><h3 style="color:#FFF;margin-bottom:8px;">${this.escapeHtml(lesson.title)}</h3><p style="color:#888;margin-bottom:8px;">${this.escapeHtml(displayName)}</p><p style="color:#666;font-size:0.85rem;margin-bottom:20px;">${this.getFileTypeLabel(fileType)}${extension ? ' (.' + extension.toUpperCase() + ')' : ''}</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;"><button onclick="learningInterface.openFileViewer('${this.escapeHtml(fileUrl).replace(/'/g, "\\'")}', '${this.escapeHtml(displayName).replace(/'/g, "\\'")}')" style="padding:12px 24px;background:rgba(139,92,246,0.15);color:#8B5CF6;border:1px solid rgba(139,92,246,0.3);border-radius:8px;cursor:pointer;font-weight:600;text-decoration:none;display:inline-block;"><i class="fas fa-eye"></i> Preview File</button><a href="${this.escapeHtml(fileUrl)}" download style="padding:12px 24px;background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.3);border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;"><i class="fas fa-download"></i> Download</a></div></div>` : '<p style="color:#888;text-align:center;padding:40px;">No file available.</p>';
                break;
            case 'live_session':
                const ls = document.getElementById('articleSection'); if (ls) ls.style.display = '';
                document.getElementById('articleTitle').textContent = lesson.title;
                document.getElementById('articleBody').innerHTML = `<div style="text-align:center;padding:40px 20px;"><i class="fas fa-video" style="font-size:4rem;color:#3B82F6;display:block;margin-bottom:16px;"></i><h3 style="color:#FFF;margin-bottom:8px;">${this.escapeHtml(lesson.title)}</h3><p style="color:#888;">Live session details will be available here.</p><p style="color:#666;font-size:0.85rem;margin-top:16px;">Join the live session at the scheduled time.</p></div>`;
                break;
            case 'coding_exercise':
                const ce = document.getElementById('articleSection'); if (ce) ce.style.display = '';
                document.getElementById('articleTitle').textContent = lesson.title;
                document.getElementById('articleBody').innerHTML = `<div style="text-align:center;padding:40px 20px;"><i class="fas fa-code" style="font-size:4rem;color:#F59E0B;display:block;margin-bottom:16px;"></i><h3 style="color:#FFF;margin-bottom:8px;">${this.escapeHtml(lesson.title)}</h3><p style="color:#888;">Coding exercise will be available here.</p></div>`;
                break;
            default:
                const ds = document.getElementById('articleSection'); if (ds) ds.style.display = '';
                document.getElementById('articleTitle').textContent = lesson.title;
                document.getElementById('articleBody').innerHTML = '<p style="color:#888;text-align:center;padding:40px;">Content type not supported.</p>';
        }

        document.getElementById('currentLessonTitle').textContent = lesson.title;
        const tb = document.querySelector('.lesson-type-badge'); if (tb) { tb.innerHTML = this.getTypeIcon(lesson.type) + ' ' + this.getTypeLabel(lesson.type); tb.className = 'lesson-type-badge ' + lesson.type; }
        const db = document.querySelector('.lesson-duration-badge'); if (db) db.innerHTML = '<i class="fas fa-clock"></i> ' + lesson.duration;
        const all = this.getAllLessons(); const fi = all.findIndex(l => l.id === lesson.id);
        document.getElementById('navLessonIndicator').textContent = `Lesson ${fi+1} of ${all.length}`;
        const mc = document.querySelector('.mobile-lesson-count'); if (mc) mc.textContent = `${fi+1} / ${all.length}`;
        this.updateBookmarkUI(); this.renderResources(lesson.resources||[]); this.updateCompleteButtonLabel();
        document.getElementById('playPauseBtn').innerHTML = '<i class="fas fa-play"></i>';
        this.updateCompletionButtonUI(lesson);

        if (this.activeTab === 'transcript' && lesson.type !== 'video') {
            this.switchTab('overview', true);
        }
    }

    renderOverviewContent(lesson) {
        const overviewPanel = document.getElementById('tabOverview');
        if (!overviewPanel) return;

        const description = lesson.description || 'No description available for this lesson.';
        const resourcesCount = lesson.resources ? lesson.resources.length : 0;

        overviewPanel.innerHTML = `
            <div style="padding:20px;">
                <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:12px;padding:24px;margin-bottom:20px;">
                    <h3 style="color:#FFF;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
                        <i class="fas fa-info-circle" style="color:#8B5CF6;"></i> About This Lesson
                    </h3>
                    <p style="color:#AAA;line-height:1.8;font-size:0.95rem;">${this.escapeHtml(description)}</p>
                </div>

                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;">
                    <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:12px;padding:20px;text-align:center;">
                        <div style="font-size:2rem;color:#8B5CF6;margin-bottom:8px;">
                            <i class="fas fa-clock"></i>
                        </div>
                        <h4 style="color:#FFF;margin-bottom:4px;">Duration</h4>
                        <p style="color:#888;font-size:0.9rem;">${this.escapeHtml(lesson.duration || 'N/A')}</p>
                    </div>

                    <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:12px;padding:20px;text-align:center;">
                        <div style="font-size:2rem;color:#10B981;margin-bottom:8px;">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <h4 style="color:#FFF;margin-bottom:4px;">Resources</h4>
                        <p style="color:#888;font-size:0.9rem;">${resourcesCount > 0 ? resourcesCount + ' file' + (resourcesCount > 1 ? 's' : '') + ' available' : 'No resources'}</p>
                    </div>

                    <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:12px;padding:20px;text-align:center;">
                        <div style="font-size:2rem;color:#F59E0B;margin-bottom:8px;">
                            <i class="fas fa-tasks"></i>
                        </div>
                        <h4 style="color:#FFF;margin-bottom:4px;">Type</h4>
                        <p style="color:#888;font-size:0.9rem;">${this.getTypeLabel(lesson.type)}</p>
                    </div>
                </div>
            </div>
        `;
    }

    updateTranscriptTabVisibility(isVideoLesson) {
        const transcriptTab = document.querySelector('.lesson-tab[data-tab="transcript"]');
        if (transcriptTab) {
            if (isVideoLesson) {
                transcriptTab.style.display = 'flex';
            } else {
                transcriptTab.style.display = 'none';
            }
        }
    }

    updateResourcesTabBadge(count) {
        const badge = document.querySelector('.lesson-tab[data-tab="resources"] .tab-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-flex';
            } else {
                badge.textContent = '0';
                badge.style.display = 'none';
            }
        }
    }

    renderTranscriptContent(lesson) {
        const transcriptPanel = document.getElementById('tabTranscript');
        if (!transcriptPanel) return;

        const transcriptData = lesson.transcript || lesson.transcriptData || null;

        if (!transcriptData) {
            transcriptPanel.innerHTML = `
                <div style="text-align:center;padding:40px 20px;">
                    <i class="fas fa-closed-captioning" style="font-size:3rem;color:#6B7280;display:block;margin-bottom:16px;"></i>
                    <h3 style="color:#FFF;margin-bottom:8px;">No Transcript Available</h3>
                    <p style="color:#888;">Transcript for this video is not available yet.</p>
                </div>
            `;
            return;
        }

        if (typeof transcriptData === 'string') {
            transcriptPanel.innerHTML = `
                <div style="padding:20px;">
                    <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:8px;padding:20px;color:#DDD;line-height:1.8;font-size:0.9rem;">
                        ${this.escapeHtml(transcriptData).replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
            return;
        }

        if (Array.isArray(transcriptData)) {
            const transcriptHTML = transcriptData.map(segment => {
                const time = segment.time || segment.timestamp || '';
                const text = segment.text || '';
                return `
                    <div class="transcript-segment" data-time="${this.escapeHtml(time)}" style="display:flex;gap:12px;padding:12px;border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer;transition:background 0.2s;" onmouseover="this.style.background='rgba(139,92,246,0.1)';" onmouseout="this.style.background='transparent';" onclick="seekToTranscriptTime('${this.escapeHtml(time)}')">
                        <span style="color:#8B5CF6;font-weight:600;min-width:60px;">${this.escapeHtml(time)}</span>
                        <span style="color:#DDD;flex:1;">${this.escapeHtml(text)}</span>
                    </div>
                `;
            }).join('');

            transcriptPanel.innerHTML = `
                <div style="padding:20px;">
                    <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:8px;overflow:hidden;">
                        ${transcriptHTML}
                    </div>
                </div>
            `;
            return;
        }

        transcriptPanel.innerHTML = `
            <div style="text-align:center;padding:40px 20px;">
                <i class="fas fa-closed-captioning" style="font-size:3rem;color:#6B7280;display:block;margin-bottom:16px;"></i>
                <h3 style="color:#FFF;margin-bottom:8px;">No Transcript Available</h3>
                <p style="color:#888;">Transcript for this video is not available yet.</p>
            </div>
        `;
    }

    seekToTranscriptTime(timeString) {
        if (!this.videoPlayer || !timeString) return;

        const parts = timeString.split(':').map(Number);
        let seconds = 0;

        if (parts.length === 3) {
            seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
        } else if (parts.length === 2) {
            seconds = parts[0] * 60 + parts[1];
        } else if (parts.length === 1) {
            seconds = parts[0];
        }

        if (seconds > 0 && this.videoPlayer.duration) {
            this.videoPlayer.currentTime = seconds;
            if (this.videoPlayer.paused) {
                this.videoPlayer.play();
            }
        }
    }

    updateCompletionButtonUI(lesson) {
        if (!lesson) return;

        const criteria = this.parseCompletionCriteria(lesson);
        const isDone = (this.progressData?.completedLessons||[]).includes(lesson.id);

        document.querySelectorAll('.mark-complete-btn, .mark-complete-btn-main').forEach(btn => {
            const parent = btn.parentElement;
            if (parent) {
                const existingStatus = parent.querySelector('.auto-completion-status');
                if (existingStatus) existingStatus.remove();
            }

            if (isDone) {
                btn.style.display = '';
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
                btn.style.background = 'rgba(16,185,129,0.25)';
                btn.style.borderColor = 'rgba(16,185,129,0.5)';
                btn.style.color = '#10B981';
                btn.style.cursor = 'default';
                btn.style.pointerEvents = 'none';
                btn.disabled = true;
            } else if (criteria.criteriaType === 'manual') {
                btn.style.display = '';
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Mark as Complete';
                btn.style.background = 'rgba(16,185,129,0.15)';
                btn.style.borderColor = 'rgba(16,185,129,0.3)';
                btn.style.color = '#10B981';
                btn.style.cursor = 'pointer';
                btn.style.pointerEvents = 'auto';
                btn.disabled = false;
            } else if (criteria.criteriaType === 'submit_assignment') {
                btn.style.display = 'none';

                if (parent && !parent.querySelector('.auto-completion-status')) {
                    const statusDiv = document.createElement('div');
                    statusDiv.className = 'auto-completion-status';
                    statusDiv.style.cssText = 'display:inline-flex;align-items:center;gap:8px;padding:10px 16px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);border-radius:8px;color:#93C5FD;font-size:0.85rem;font-weight:500;';
                    statusDiv.innerHTML = '📤 Waiting for instructor review';
                    parent.appendChild(statusDiv);
                }
            } else {
                btn.style.display = 'none';

                if (parent && !parent.querySelector('.auto-completion-status')) {
                    const statusDiv = document.createElement('div');
                    statusDiv.className = 'auto-completion-status';
                    statusDiv.style.cssText = 'display:inline-flex;align-items:center;gap:8px;padding:10px 16px;background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);border-radius:8px;color:#A78BFA;font-size:0.85rem;font-weight:500;';

                    let statusText = '';
                    switch(criteria.criteriaType) {
                        case 'watch_video':
                            statusText = `📺 Watch ${criteria.videoWatchPercentage}% to complete`;
                            break;
                        case 'read_article':
                            statusText = `📖 Read ${criteria.articleScrollPercentage}% to complete`;
                            break;
                        case 'pass_quiz':
                            statusText = `📝 Pass quiz (${criteria.quizPassingScore}%) to complete`;
                            break;
                        case 'submit_assignment':
                            statusText = '📤 Submit assignment for review';
                            break;
                        default:
                            statusText = 'Complete requirements to finish';
                    }

                    statusDiv.innerHTML = statusText;
                    parent.appendChild(statusDiv);
                }
            }
        });
    }

    async handleManualCompletion() {
        const lesson = this.getCurrentLesson();
        if (!lesson) return;

        const criteria = this.parseCompletionCriteria(lesson);

        if (criteria.criteriaType !== 'manual') {
            this.showToast('This lesson will auto-complete when requirements are met');
            return;
        }

        await this.markLessonComplete(false);
    }

    updateCompleteButtonLabel() {
        const lesson = this.getCurrentLesson(); if (!lesson) return;
        const criteria = this.parseCompletionCriteria(lesson);
        const label = this.getCompletionActionLabel(lesson);
        const isDone = (this.progressData?.completedLessons||[]).includes(lesson.id);

        document.querySelectorAll('.mark-complete-btn, .mark-complete-btn-main').forEach(btn => {
            if (isDone) {
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
            } else if (criteria.criteriaType === 'manual') {
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Mark as Complete';
            } else {
                btn.style.display = 'none';
            }
        });
    }

    setCompleteButtonState(isDone) {
        const lesson = this.getCurrentLesson();
        if (!lesson) return;

        const criteria = this.parseCompletionCriteria(lesson);

        document.querySelectorAll('.mark-complete-btn, .mark-complete-btn-main').forEach(btn => {
            if (isDone) {
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
                btn.style.background = 'rgba(16,185,129,0.25)';
                btn.style.borderColor = 'rgba(16,185,129,0.5)';
                btn.style.color = '#10B981';
                btn.style.display = '';
                btn.disabled = true;
            } else if (criteria.criteriaType === 'manual') {
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Mark as Complete';
                btn.style.background = 'rgba(16,185,129,0.15)';
                btn.style.borderColor = 'rgba(16,185,129,0.3)';
                btn.style.color = '#10B981';
                btn.style.display = '';
                btn.disabled = false;
            } else {
                btn.style.display = 'none';
            }
        });
    }

    updateSidebarActive() {
        document.querySelectorAll('.curriculum-lesson-item').forEach(el => {
            el.classList.remove('active');
            if (parseInt(el.dataset.lesson) === this.currentLessonId) {
                el.classList.add('active');
                const lc = el.closest('.curriculum-lessons');
                if (lc && lc.style.display === 'none') {
                    lc.style.display = '';
                    lc.previousElementSibling?.classList.add('open');
                }
            }
        });
    }

    renderResources(resources) {
        const c = document.querySelector('.resources-area'); if (!c) return;
        const normalizedResources = this.normalizeResources(resources);

        this.updateResourcesTabBadge(normalizedResources.length);

        if (!normalizedResources.length) {
            c.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">No resources available.</p>';
            return;
        }
        c.innerHTML = normalizedResources.map(r => `<div class="resource-item-card"><div class="resource-icon"><i class="fas ${this.getResourceIconClass(r.type || 'zip')}"></i></div><div class="resource-info"><span class="resource-name">${this.escapeHtml(r.name)}</span><span class="resource-size">${this.escapeHtml(r.size)}</span></div><a href="${r.url || '#'}" class="resource-download-btn" download="${this.escapeHtml(r.name)}"><i class="fas fa-download"></i> Download</a></div>`).join('');

        const badge = document.querySelector('.lesson-tab[data-tab="resources"] .tab-badge');
        if (badge) {
            badge.textContent = normalizedResources.length;
            badge.style.display = normalizedResources.length > 0 ? 'inline-flex' : 'none';
        }
    }

    prepareQuizQuestions(lesson) {
        if (!lesson.quizData?.questions) return;
        this.quizQuestionsWithoutCorrect = lesson.quizData.questions.map(q => ({
            id: q.id,
            text: q.text,
            question_type: q.question_type||'single_choice',
            choices: q.choices||[],
            explanation: q.explanation||'',
            points: q.points||1
        }));
        lesson.quizData.questions = this.quizQuestionsWithoutCorrect;
        if (lesson.completion_criteria?.quiz_passing_score) lesson.quizData.passScore = lesson.completion_criteria.quiz_passing_score;

        if (lesson.quizData.max_attempts) {
            this.maxQuizAttempts = lesson.quizData.max_attempts;
        }
    }

    resetQuizState() {
        this.currentQuizIndex=0;
        this.quizScore=0;
        this.quizUserAnswers=[];
        this.quizResultData=null;
        this.isQuizSubmitting=false;
        this.quizCompleted=false;
        this.quizQuestionsWithoutCorrect=[];
        this.quizPhase = 'answering';
        this.quizAttemptsExhausted = false;
    }

    buildQuizUI() {
        const qs = document.getElementById('quizSection'); if (!qs) return;
        const lesson = this.getCurrentLesson(); if (!lesson?.quizData) return;
        const passScore = (this.parseCompletionCriteria(lesson)).quizPassingScore||60;
        const questions = lesson.quizData.questions;

        const typeCounts = {}; questions.forEach(q => { const t = q.question_type||'single_choice'; typeCounts[t] = (typeCounts[t]||0)+1; });
        let typeSummary = ''; for (const [t, c] of Object.entries(typeCounts)) typeSummary += `<span style="margin-right:12px;font-size:0.8rem;color:#888;">${this.getQuestionTypeIcon(t)} ${c} ${this.getQuestionTypeLabel(t)}</span>`;

        const completedLessons = this.progressData?.completedLessons || [];
        const isCompleted = completedLessons.includes(lesson.id);

        qs.innerHTML = `<div class="quiz-container"><div class="quiz-header"><h2 class="quiz-title" id="quizTitle">${this.escapeHtml(lesson.title)}</h2><div class="quiz-meta"><span><i class="fas fa-circle-question"></i> ${questions.length} Questions</span><span><i class="fas fa-trophy"></i> Pass: ${passScore}%</span><span><i class="fas fa-redo"></i> Attempts: ${this.quizAttemptsUsed}/${this.maxQuizAttempts}</span>${this.quizBestScore > 0 ? `<span><i class="fas fa-star"></i> Best Score: ${this.quizBestScore}%</span>` : ''}</div><div style="margin-top:8px;">${typeSummary}</div></div><div class="quiz-question-card" id="quizQuestionCard" style="display:none;"><div class="quiz-q-header"><span class="quiz-q-number"></span><span class="quiz-q-points"></span><span class="quiz-q-type" id="quizQuestionType" style="margin-left:12px;font-size:0.8rem;color:#8B5CF6;"></span></div><p class="quiz-q-text"></p><p id="quizQuestionInstruction" style="color:#666;font-size:0.8rem;margin-bottom:12px;"></p><div class="quiz-options" id="quizOptionsContainer"></div><div class="quiz-actions" style="display:flex;gap:12px;margin-top:20px;"><button type="button" class="quiz-btn quiz-btn-secondary" id="quizPrevBtn" style="display:none;">← Previous</button><button type="button" class="quiz-btn quiz-btn-secondary" id="quizSkipBtn">Skip</button><button type="button" class="quiz-btn quiz-btn-primary" id="quizSubmitBtn">Submit & Next</button></div></div><div id="quizLoadingSpinner" style="display:none;text-align:center;padding:60px;"><div style="display:inline-block;width:50px;height:50px;border:4px solid #2A2A3E;border-top-color:#8B5CF6;border-radius:50%;animation:spin 0.8s linear infinite;"></div><h3 style="color:#FFF;margin:12px 0;">Evaluating...</h3></div><div id="quizFinalResult" style="display:none;"></div></div><style>@keyframes spin{to{transform:rotate(360deg)}}.quiz-btn{padding:12px 24px;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9rem;border:none;display:inline-block;}.quiz-btn-primary{background:linear-gradient(135deg,#8B5CF6,#7C3AED);color:#FFF;}.quiz-btn-secondary{background:rgba(255,255,255,0.06);color:#AAA;border:1px solid #2A2A3E;}.quiz-option{display:flex;align-items:center;gap:12px;padding:14px 16px;background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:8px;cursor:pointer;margin-bottom:8px;}.quiz-option.selected{border-color:#8B5CF6!important;background:rgba(139,92,246,0.1)!important;}.quiz-option-letter{width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:rgba(139,92,246,0.15);color:#A78BFA;border-radius:50%;font-weight:600;font-size:0.85rem;flex-shrink:0;}.quiz-option-text{color:#DDD;flex:1;}</style>`;
        this.setupQuizEventDelegation();

        if (isCompleted && this.quizBestScore >= passScore) {
            this.quizPhase = 'results';
            this.quizCompleted = true;
            document.getElementById('quizQuestionCard').style.display = 'none';
            this.displayPassedQuizPlaceholder();
        } else if (!this.quizCanAttempt) {
            this.quizPhase = 'results';
            this.quizAttemptsExhausted = true;
            document.getElementById('quizQuestionCard').style.display = 'none';
            this.displayMaxAttemptsExhausted();
        } else {
            this.quizPhase = 'answering';
            document.getElementById('quizQuestionCard').style.display = 'block';
            this.renderQuizQuestion();
        }
    }

    displayPassedQuizPlaceholder() {
        const fd = document.getElementById('quizFinalResult');
        fd.style.display = 'block';

        fd.innerHTML = `
            <div style="text-align:center;padding:30px;">
                <div style="margin-bottom:20px;">
                    <i class="fas fa-check-circle" style="font-size:4rem;color:#10B981;"></i>
                </div>
                <h2 style="color:#FFF;">Quiz Completed! 🎉</h2>
                <p style="color:#AAA;margin:20px 0;">You have already passed this quiz.</p>
                ${this.quizBestScore > 0 ? `<p style="color:#F59E0B;font-size:1.2rem;">Best Score: ${this.quizBestScore}%</p>` : ''}
                ${this.quizCanAttempt ? `<p style="color:#8B5CF6;margin-top:10px;">You can retry to improve your score (${this.quizAttemptsRemaining} attempts remaining)</p><button type="button" id="quizRetryFromResultBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(139,92,246,0.2);color:#8B5CF6;">Retry Quiz</button>` : ''}
                <div style="display:flex;gap:12px;justify-content:center;margin-top:20px;">
                    <button type="button" id="quizContinueAfterPassBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(16,185,129,0.2);color:#10B981;">Continue →</button>
                </div>
            </div>
        `;
    }

    displayMaxAttemptsExhausted() {
        const fd = document.getElementById('quizFinalResult');
        fd.style.display = 'block';

        fd.innerHTML = `
            <div style="text-align:center;padding:30px;">
                <div style="margin-bottom:20px;">
                    <i class="fas fa-exclamation-circle" style="font-size:4rem;color:#EF4444;"></i>
                </div>
                <h2 style="color:#FFF;">Maximum Attempts Reached</h2>
                <p style="color:#AAA;margin:20px 0;">You have used all ${this.maxQuizAttempts} attempts for this quiz.</p>
                ${this.quizBestScore > 0 ? `<p style="color:#F59E0B;font-size:1.2rem;">Best Score: ${this.quizBestScore}%</p>` : ''}
            </div>
        `;
    }

    renderQuizQuestion() {
        const lesson = this.getCurrentLesson(); if (!lesson?.quizData) return;
        const q = lesson.quizData.questions[this.currentQuizIndex]; if (!q) return;
        ['quizLoadingSpinner','quizFinalResult'].forEach(id => document.getElementById(id).style.display='none');
        document.getElementById('quizQuestionCard').style.display='block';
        document.querySelector('.quiz-q-number').textContent = `Question ${this.currentQuizIndex+1} of ${lesson.quizData.questions.length}`;
        document.querySelector('.quiz-q-text').textContent = q.text;
        document.getElementById('quizQuestionType').innerHTML = this.getQuestionTypeIcon(q.question_type) + ' ' + this.getQuestionTypeLabel(q.question_type);
        document.getElementById('quizQuestionInstruction').textContent = this.getQuestionInstruction(q.question_type);
        document.querySelector('.quiz-q-points').textContent = `${q.points||1} point${q.points>1?'s':''}`;
        const ea = this.quizUserAnswers.find(a => a.questionId === q.id);
        const oc = document.getElementById('quizOptionsContainer');
        switch(q.question_type) { case 'single_choice': this.renderSingleChoice(oc, q, ea); break; case 'multiple_choice': this.renderMultipleChoice(oc, q, ea); break; case 'true_false': this.renderTrueFalse(oc, q, ea); break; case 'short_answer': this.renderShortAnswer(oc, q, ea); break; }
        this.updateQuizNavButtons();
    }

    renderSingleChoice(c, q, ea) {
        const sv = ea?.selectedValues?.[0];
        c.innerHTML = (q.choices||[]).map((ch) => `<label class="quiz-option${sv === String(ch.id) ? ' selected':''}"><input type="radio" name="qa" value="${ch.id}"${sv === String(ch.id) ? ' checked':''} style="display:none;"><span class="quiz-option-letter">${String.fromCharCode(64 + parseInt(ch.id))}</span><span class="quiz-option-text">${this.escapeHtml(ch.text)}</span></label>`).join('');
        c.querySelectorAll('.quiz-option').forEach(l => l.addEventListener('click', function(){c.querySelectorAll('.quiz-option').forEach(o=>o.classList.remove('selected'));this.classList.add('selected');this.querySelector('input').checked=true;}));
    }
    renderMultipleChoice(c, q, ea) {
        const sv = ea?.selectedValues || [];
        c.innerHTML = (q.choices||[]).map((ch) => `<label class="quiz-option${sv.includes(String(ch.id)) ? ' selected':''}"><input type="checkbox" name="qa" value="${ch.id}"${sv.includes(String(ch.id)) ? ' checked':''} style="display:none;"><span class="quiz-option-letter">${String.fromCharCode(64 + parseInt(ch.id))}</span><span class="quiz-option-text">${this.escapeHtml(ch.text)}</span><span class="cm" style="color:${sv.includes(String(ch.id)) ? '#8B5CF6':'transparent'};">✓</span></label>`).join('');
        c.querySelectorAll('.quiz-option').forEach(l => l.addEventListener('click', function(){const cb=this.querySelector('input');cb.checked=!cb.checked;const m=this.querySelector('.cm');if(cb.checked){this.classList.add('selected');if(m)m.style.color='#8B5CF6';}else{this.classList.remove('selected');if(m)m.style.color='transparent';}}));
    }
    renderTrueFalse(c, q, ea) {
        const sv = ea?.boolValue;
        c.innerHTML = ['True','False'].map(o => `<label class="quiz-option${sv===o?' selected':''}" style="padding:20px;"><input type="radio" name="qa" value="${o}"${sv===o?' checked':''} style="display:none;"><span style="font-size:2rem;color:${o==='True'?'#10B981':'#EF4444'};">${o==='True'?'✓':'✗'}</span><span style="color:#DDD;font-size:1.2rem;font-weight:600;">${o}</span></label>`).join('');
        c.querySelectorAll('.quiz-option').forEach(l => l.addEventListener('click', function(){c.querySelectorAll('.quiz-option').forEach(o=>o.classList.remove('selected'));this.classList.add('selected');this.querySelector('input').checked=true;}));
    }
    renderShortAnswer(c, q, ea) {
        const t = ea?.textAnswer||'';
        c.innerHTML = `<textarea id="shortAnswerInput" class="short-answer-textarea" placeholder="Type your answer..." rows="5" style="width:100%;background:rgba(255,255,255,0.05);border:1px solid #2A2A3E;border-radius:8px;color:#FFF;padding:12px 16px;font-size:0.95rem;resize:vertical;min-height:120px;outline:none;box-sizing:border-box;">${this.escapeHtml(t)}</textarea><div style="display:flex;justify-content:space-between;margin-top:8px;"><span style="color:#666;font-size:0.75rem;">Ctrl+Enter to submit</span><span id="charCount" style="color:#666;font-size:0.75rem;">${t.length} chars</span></div>`;
        setTimeout(()=>{const ta=document.getElementById('shortAnswerInput');if(ta){ta.addEventListener('input',()=>{const cc=document.getElementById('charCount');if(cc)cc.textContent=ta.value.length+' chars';});ta.focus();}},100);
    }

    updateQuizNavButtons() { const t = this.getCurrentLesson()?.quizData?.questions?.length||0; document.getElementById('quizPrevBtn').style.display = this.currentQuizIndex===0?'none':'inline-block'; document.getElementById('quizSkipBtn').style.display = this.currentQuizIndex>=t-1?'none':'inline-block'; const sb = document.getElementById('quizSubmitBtn'); if (sb) { sb.textContent = this.currentQuizIndex>=t-1?'Submit Quiz':'Submit & Next'; sb.style.background = this.currentQuizIndex>=t-1?'linear-gradient(135deg,#10B981,#059669)':'linear-gradient(135deg,#8B5CF6,#7C3AED)'; } }
    handleQuizPrevious() { if(this.currentQuizIndex>0){this.saveCurrentQuizAnswer();this.currentQuizIndex--;this.renderQuizQuestion();} }
    handleQuizSkip() { const t=this.getCurrentLesson()?.quizData?.questions?.length||0; if(this.currentQuizIndex<t-1){this.saveCurrentQuizAnswer();this.currentQuizIndex++;this.renderQuizQuestion();} }

    saveCurrentQuizAnswer() {
        const q = this.getCurrentLesson()?.quizData?.questions?.[this.currentQuizIndex]; if (!q) return;
        let a = { questionId: q.id, questionType: q.question_type||'single_choice' };
        switch(q.question_type) {
            case 'single_choice':
            case 'true_false': {
                const r = document.querySelector('input[name="qa"]:checked');
                if (r) {
                    if (q.question_type === 'true_false') {
                        a.boolValue = r.value;
                    } else {
                        a.selectedValues = [r.value];
                    }
                }
                break;
            }
            case 'multiple_choice': {
                const cs = document.querySelectorAll('input[name="qa"]:checked');
                if (cs.length) a.selectedValues = Array.from(cs).map(c => c.value);
                break;
            }
            case 'short_answer': {
                const ta = document.getElementById('shortAnswerInput');
                if (ta) a.textAnswer = ta.value.trim();
                break;
            }
        }
        const idx = this.quizUserAnswers.findIndex(x=>x.questionId===q.id); if(idx>=0) this.quizUserAnswers[idx]=a; else this.quizUserAnswers.push(a);
    }

    handleQuizAnswerSubmit() {
        const q = this.getCurrentLesson()?.quizData?.questions?.[this.currentQuizIndex]; if (!q) return;
        let valid=false, msg='';
        switch(q.question_type) {
            case 'single_choice':
            case 'true_false':
                valid=!!document.querySelector('input[name="qa"]:checked');
                msg='Select an answer';
                break;
            case 'multiple_choice':
                valid=document.querySelectorAll('input[name="qa"]:checked').length>0;
                msg='Select at least one';
                break;
            case 'short_answer': {
                const ta=document.getElementById('shortAnswerInput');
                valid=ta?ta.value.trim().length>0:false;
                msg='Type your answer';
                break;
            }
        }
        if(!valid){this.showToast(msg);return;} this.saveCurrentQuizAnswer();
        const t = this.getCurrentLesson()?.quizData?.questions?.length||0;
        if(this.currentQuizIndex>=t-1) this.submitQuizToBackend(); else { this.currentQuizIndex++; this.renderQuizQuestion(); }
    }

    async submitQuizToBackend() {
        const l = this.getCurrentLesson(); if(!l?.quizData||this.isQuizSubmitting) return;

        if (!this.quizCanAttempt) {
            this.quizAttemptsExhausted = true;
            this.displayMaxAttemptsExhausted();
            return;
        }

        this.isQuizSubmitting=true; this.saveCurrentQuizAnswer();
        document.getElementById('quizQuestionCard').style.display='none'; document.getElementById('quizLoadingSpinner').style.display='block';
        try {
            const result = await ApiService.submitQuizAnswers(this.enrollmentId, l.id, this.quizUserAnswers);
            this.quizResultData = result;
            this.quizScore = result.score || 0;
            this.quizCompleted = true;
            this.quizPhase = 'results';

            if (result.max_attempts) {
                this.maxQuizAttempts = result.max_attempts;
            }
            if (result.attempts_used) {
                this.quizAttemptsUsed = result.attempts_used;
            }
            if (result.attempts_remaining !== undefined) {
                this.quizAttemptsRemaining = result.attempts_remaining;
            }
            if (result.best_score) {
                this.quizBestScore = result.best_score;
            }
            this.quizCanAttempt = result.attempts_remaining > 0;

            if (result.lessonCompleted && result.completedLessons) {
                this.progressData.completedLessons = result.completedLessons;
                this.progressData.completedCount = result.completedCount || result.completedLessons.length;
                this.progressData.overallProgress = result.overallProgress || Math.round((result.completedLessons.length / (this.courseData?.totalLessons || 12)) * 100);

                this.updateProgressUI();
                this.renderSidebar();
                this.setCompleteButtonState(true);

                if (result.passed) {
                    this.showToast('🎉 Quiz passed - Lesson completed!');
                }
            }

            this.displayQuizResult(result);

        } catch(e) {
            document.getElementById('quizLoadingSpinner').style.display='none';
            document.getElementById('quizQuestionCard').style.display='block';
            document.getElementById('quizQuestionCard').innerHTML = `<div style="text-align:center;padding:40px;"><i class="fas fa-exclamation-triangle" style="font-size:3rem;color:#EF4444;"></i><h3 style="color:#FFF;">Failed</h3><button type="button" id="quizRetrySubmitBtn" class="quiz-btn quiz-btn-primary">Retry</button></div>`;
        } finally { this.isQuizSubmitting=false; }
    }

    handleQuizContinue() {
        const all = this.getAllLessons();
        const idx = all.findIndex(l => l.id === this.currentLessonId);
        if (idx >= 0 && idx < all.length - 1) {
            this.navigateToLessonById(all[idx + 1].id);
        }
    }

    displayQuizResult(r) {
        document.getElementById('quizLoadingSpinner').style.display='none';
        const fd=document.getElementById('quizFinalResult');
        fd.style.display='block';

        const includeCorrectAnswers = r.includeCorrectAnswers !== undefined ? r.includeCorrectAnswers : true;

        if (includeCorrectAnswers) {
            fd.innerHTML = this.buildDetailedQuizResultHTML(r);
        } else {
            fd.innerHTML = this.buildSimpleQuizResultHTML(r);
        }
    }

    buildDetailedQuizResultHTML(r) {
        const questions = this.getCurrentLesson()?.quizData?.questions || [];
        const questionResults = r.questionResults || [];

        let incorrectAnswersHTML = '';
        const incorrectAnswers = questionResults.filter(q => !q.isCorrect);

        if (incorrectAnswers.length > 0) {
            incorrectAnswersHTML = `
                <div style="margin-top:20px;text-align:left;">
                    <h4 style="color:#EF4444;margin-bottom:12px;">Incorrect Answers:</h4>
                    ${incorrectAnswers.map(wq => {
                        const question = questions.find(q => q.id === wq.questionId);
                        const questionText = question ? question.text : `Question ${wq.questionId}`;
                        const userAnswerDisplay = this.formatAnswerDisplay(wq.userAnswer, wq.questionType);
                        const correctAnswerDisplay = this.formatAnswerDisplay(wq.correctAnswer, wq.questionType);

                        return `
                            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px;margin-bottom:8px;">
                                <p style="color:#DDD;margin:0 0 8px 0;"><strong>Q:</strong> ${this.escapeHtml(questionText)}</p>
                                <p style="color:#EF4444;margin:0 0 4px 0;"><strong>Your answer:</strong> ${userAnswerDisplay}</p>
                                <p style="color:#10B981;margin:0;"><strong>Correct answer:</strong> ${correctAnswerDisplay}</p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        const canRetry = this.quizCanAttempt;

        return `
            <div style="text-align:center;padding:30px;">
                <div style="margin-bottom:20px;">
                    ${r.passed?'<i class="fas fa-trophy" style="font-size:4rem;color:#F59E0B;"></i>':'<i class="fas fa-times-circle" style="font-size:4rem;color:#EF4444;"></i>'}
                </div>
                <h2 style="color:#FFF;">${r.passed?'Passed! 🎉':'Not Passed'}</h2>
                <div style="margin:20px 0;">
                    <span style="font-size:3rem;font-weight:700;color:${r.passed?'#10B981':'#EF4444'};">${r.percentage}%</span>
                    <span style="color:#888;display:block;">${r.score}/${r.totalQuestions} correct</span>
                    <span style="color:#666;display:block;margin-top:8px;">Attempts: ${this.quizAttemptsUsed}/${this.maxQuizAttempts}</span>
                    ${this.quizBestScore > 0 ? `<span style="color:#F59E0B;display:block;margin-top:4px;">★ Best Score: ${this.quizBestScore}%</span>` : ''}
                    ${r.lessonCompleted ? '<span style="color:#10B981;display:block;margin-top:4px;">✓ Lesson marked as complete</span>' : ''}
                </div>
                <p style="color:#AAA;">${r.message}</p>
                ${incorrectAnswersHTML}
                <div style="display:flex;gap:12px;justify-content:center;margin-top:20px;flex-wrap:wrap;">
                    ${canRetry
                        ? `<button type="button" id="quizRetryFromResultBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(139,92,246,0.2);color:#8B5CF6;">Retry Quiz (${this.quizAttemptsRemaining} attempts left)</button>`
                        : '<p style="color:#EF4444;">No more attempts available</p>'
                    }
                    ${r.passed
                        ? '<button type="button" id="quizContinueAfterPassBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(16,185,129,0.2);color:#10B981;">Continue →</button>'
                        : ''
                    }
                </div>
            </div>
        `;
    }

    buildSimpleQuizResultHTML(r) {
        const questionResults = r.questionResults || [];
        const wrongCount = questionResults.filter(q => !q.isCorrect).length;
        const canRetry = this.quizCanAttempt;

        return `
            <div style="text-align:center;padding:30px;">
                <div style="margin-bottom:20px;">
                    ${r.passed?'<i class="fas fa-trophy" style="font-size:4rem;color:#F59E0B;"></i>':'<i class="fas fa-times-circle" style="font-size:4rem;color:#EF4444;"></i>'}
                </div>
                <h2 style="color:#FFF;">${r.passed?'Passed! 🎉':'Not Passed'}</h2>
                <div style="margin:20px 0;">
                    <span style="font-size:3rem;font-weight:700;color:${r.passed?'#10B981':'#EF4444'};">${r.percentage}%</span>
                    <span style="color:#888;display:block;">${r.score}/${r.totalQuestions} correct</span>
                    <span style="color:#666;display:block;margin-top:8px;">Attempts: ${this.quizAttemptsUsed}/${this.maxQuizAttempts}</span>
                    ${this.quizBestScore > 0 ? `<span style="color:#F59E0B;display:block;margin-top:4px;">★ Best Score: ${this.quizBestScore}%</span>` : ''}
                    ${r.lessonCompleted ? '<span style="color:#10B981;display:block;margin-top:4px;">✓ Lesson marked as complete</span>' : ''}
                </div>
                <p style="color:#AAA;">${r.message}</p>
                ${wrongCount > 0 ? `<p style="color:#EF4444;margin-top:10px;">You got ${wrongCount} question${wrongCount > 1 ? 's' : ''} wrong.</p>` : ''}
                <div style="display:flex;gap:12px;justify-content:center;margin-top:20px;">
                    ${canRetry
                        ? '<button type="button" id="quizRetryFromResultBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(139,92,246,0.2);color:#8B5CF6;">Retry Quiz</button>'
                        : '<p style="color:#EF4444;">No more attempts available</p>'
                    }
                    ${r.passed
                        ? '<button type="button" id="quizContinueAfterPassBtn" class="quiz-btn quiz-btn-primary" style="background:rgba(16,185,129,0.2);color:#10B981;">Continue →</button>'
                        : ''
                    }
                </div>
            </div>
        `;
    }

    formatAnswerDisplay(answer, questionType) {
        if (!answer || answer === 'No answer') return 'No answer';

        if (Array.isArray(answer)) {
            return answer.join(', ');
        } else if (typeof answer === 'object') {
            return JSON.stringify(answer);
        }

        return String(answer);
    }

    retryQuiz(){
        if (!this.quizCanAttempt) {
            this.showToast(`Maximum attempts (${this.maxQuizAttempts}) reached`);
            return;
        }

        this.currentQuizIndex=0;
        this.quizScore=0;
        this.quizUserAnswers=[];
        this.quizResultData=null;
        this.quizCompleted=false;
        this.isQuizSubmitting=false;
        this.quizPhase = 'answering';
        this.quizAttemptsExhausted = false;
        this.buildQuizUI();
        this.showToast(`Quiz restarted! Attempt ${this.quizAttemptsUsed + 1}/${this.maxQuizAttempts}`);
    }

buildAssignmentUI() {
    const asg = document.getElementById('assignmentSection');
    if (!asg) return;
    const lesson = this.getCurrentLesson();
    if (!lesson?.assignmentData) return;

    const data = this.assignmentData || lesson.assignmentData;
    const submissions = this.assignmentSubmissions || [];
    const maxAttempts = data.maxAttempts || 1;
    const canSubmit = submissions.length < maxAttempts;

    let submissionsHTML = '';
    if (submissions.length > 0) {
        submissionsHTML = `
            <div style="margin-top:24px;">
                <h4 style="color:#FFF;margin-bottom:12px;">Previous Submissions:</h4>
                ${submissions.map(sub => {
                    const fileUrl = sub.files && sub.files.length > 0 ? sub.files.map(f => {
                        const fileUrl = f.file || f.url || '';
                        const fileName = f.name || this.getDisplayFileName(fileUrl, '');
                        return `<a href="${this.escapeHtml(fileUrl)}" download="${this.escapeHtml(fileName)}" style="display:inline-flex;align-items:center;margin-right:8px;padding:6px 10px;background:rgba(139,92,246,0.1);border-radius:4px;font-size:0.8rem;color:#A78BFA;text-decoration:none;gap:6px;"><i class="fas fa-file-download"></i> ${this.escapeHtml(fileName)}</a>`;
                    }).join('') : '';

                    let scoreHTML = '';
                    if (sub.score !== null && sub.score !== undefined) {
                        const scoreColor = sub.score < data.passingScore ? '#EF4444' : '#10B981';
                        scoreHTML = `<span style="color:${scoreColor};">Score: ${sub.score}/${data.maxScore}</span>`;
                    }

                    return `
                        <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:8px;padding:16px;margin-bottom:12px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                                <span style="color:#8B5CF6;font-weight:600;">Attempt ${sub.attemptNumber}</span>
                                <span style="padding:4px 12px;border-radius:20px;font-size:0.75rem;background:${this.getAssignmentStatusColor(sub.status)};color:#FFF;">${this.capitalize(sub.status)}</span>
                            </div>
                            ${sub.submissionText ? `<p style="color:#AAA;margin:8px 0;">${this.escapeHtml(sub.submissionText)}</p>` : ''}
                            ${sub.files && sub.files.length > 0 ? `
                                <div style="margin:8px 0;">
                                    ${fileUrl}
                                </div>
                            ` : ''}
                            <div style="display:flex;gap:16px;margin-top:8px;font-size:0.8rem;color:#666;">
                                <span>Submitted: ${sub.submittedAt ? new Date(sub.submittedAt).toLocaleString() : 'N/A'}</span>
                                ${scoreHTML}
                                ${sub.gradedAt ? `<span>Graded: ${new Date(sub.gradedAt).toLocaleString()}</span>` : ''}
                            </div>
                            ${sub.feedback ? `<div style="margin-top:8px;padding:8px;background:rgba(16,185,129,0.1);border-radius:4px;"><span style="color:#10B981;">Feedback:</span> ${this.escapeHtml(sub.feedback)}</div>` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    let submissionFormHTML = '';
    if (canSubmit) {
        submissionFormHTML = `
            <div style="margin-top:24px;background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:8px;padding:20px;">
                <h4 style="color:#FFF;margin-bottom:12px;">Submit Assignment (Attempt ${submissions.length + 1} of ${maxAttempts})</h4>
                <textarea id="assignmentSubmissionText" placeholder="Write your submission text here (optional)..." rows="5" style="width:100%;background:rgba(255,255,255,0.05);border:1px solid #2A2A3E;border-radius:8px;color:#FFF;padding:12px 16px;font-size:0.95rem;resize:vertical;min-height:100px;outline:none;box-sizing:border-box;margin-bottom:12px;"></textarea>
                <input type="file" id="assignmentFileInput" multiple style="display:none;" accept="${this.escapeHtml(data.acceptedFileTypes || '')}">
                <div id="selectedFilesList" style="margin-bottom:12px;"></div>
                <div style="display:flex;gap:12px;flex-wrap:wrap;">
                    <button type="button" id="assignmentFileInputBtn" class="quiz-btn quiz-btn-secondary"><i class="fas fa-paperclip"></i> Attach Files</button>
                    <button type="button" id="assignmentSubmitBtn" class="quiz-btn quiz-btn-primary">Submit Assignment</button>
                </div>
                <p style="color:#666;font-size:0.75rem;margin-top:8px;">
                    Accepted file types: ${data.acceptedFileTypes || 'Any'} | Max file size: ${data.maxFileSizeMB || 50}MB
                </p>
            </div>
        `;
    } else {
        submissionFormHTML = `
            <div style="margin-top:24px;text-align:center;padding:20px;background:rgba(239,68,68,0.1);border-radius:8px;">
                <p style="color:#EF4444;">Maximum attempts reached. You cannot submit anymore.</p>
            </div>
        `;
    }

    asg.innerHTML = `
        <div class="assignment-container" style="padding:20px;">
            <div style="background:rgba(255,255,255,0.03);border:1px solid #2A2A3E;border-radius:12px;padding:24px;margin-bottom:20px;">
                <h3 style="color:#FFF;margin-bottom:16px;">Assignment Details</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:16px;">
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Passing Score:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.passingScore || 100} points</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Max Score:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.maxScore || 100} points</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Due Date:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.dueDate ? new Date(data.dueDate).toLocaleString() : 'No due date'}</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Maximum Attempts:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${maxAttempts === 0 ? 'Unlimited' : maxAttempts}</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Accepted File Types:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.acceptedFileTypes || 'Any'}</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Max File Size:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.maxFileSizeMB || 50} MB</p>
                    </div>
                    <div>
                        <span style="color:#888;font-size:0.8rem;">Late Submission:</span>
                        <p style="color:#FFF;font-weight:600;margin:4px 0 0;">${data.allowLateSubmission ? 'Allowed' : 'Not Allowed'}</p>
                    </div>
                </div>
                <div style="margin-top:16px;">
                    <span style="color:#888;font-size:0.8rem;">Instructions:</span>
                    <div style="color:#DDD;margin-top:8px;line-height:1.6;">${this.escapeHtml(data.instructions || 'No instructions provided.')}</div>
                </div>
            </div>
            ${submissionsHTML}
            ${submissionFormHTML}
        </div>
    `;
    this.setupAssignmentEventDelegation();
}

    getAssignmentStatusColor(status) {
        const colors = {
            'draft': 'rgba(107,114,128,0.5)',
            'submitted': 'rgba(59,130,246,0.5)',
            'graded': 'rgba(16,185,129,0.5)',
            'returned': 'rgba(245,158,11,0.5)',
            'late': 'rgba(239,68,68,0.5)'
        };
        return colors[status] || 'rgba(107,114,128,0.5)';
    }

    triggerFileInput() {
        const fileInput = document.getElementById('assignmentFileInput');
        if (fileInput) {
            fileInput.click();
        }
    }

    handleFileSelection(files) {
        if (!files || files.length === 0) return;
        const data = this.assignmentData;
        const maxSizeMB = data?.maxFileSizeMB || 50;
        const acceptedTypes = data?.acceptedFileTypes ? data.acceptedFileTypes.split(',') : [];

        this.selectedFiles = [];
        const selectedFilesList = document.getElementById('selectedFilesList');

        for (const file of files) {
            const fileSizeMB = file.size / (1024 * 1024);
            if (fileSizeMB > maxSizeMB) {
                this.showToast(`File ${file.name} exceeds max size of ${maxSizeMB}MB`);
                continue;
            }

            if (acceptedTypes.length > 0) {
                const fileExt = file.name.split('.').pop().toLowerCase();
                if (!acceptedTypes.includes(fileExt) && !acceptedTypes.includes('*')) {
                    this.showToast(`File type .${fileExt} not accepted`);
                    continue;
                }
            }

            this.selectedFiles.push(file);
        }

        if (selectedFilesList) {
            if (this.selectedFiles.length > 0) {
                selectedFilesList.innerHTML = this.selectedFiles.map(f => `
                    <span style="display:inline-flex;align-items:center;margin-right:8px;padding:6px 10px;background:rgba(139,92,246,0.1);border-radius:4px;font-size:0.8rem;color:#A78BFA;gap:6px;">
                        <i class="fas fa-file"></i> ${this.escapeHtml(f.name)} (${this.formatFileSize(f.size)})
                    </span>
                `).join('');
            } else {
                selectedFilesList.innerHTML = '';
            }
        }
    }

    async handleAssignmentSubmit() {
        if (this.isAssignmentSubmitting) return;

        const submissionText = document.getElementById('assignmentSubmissionText')?.value?.trim() || '';
        const data = this.assignmentData;
        const submissions = this.assignmentSubmissions || [];
        const maxAttempts = data?.maxAttempts || 1;

        if (submissions.length >= maxAttempts && maxAttempts > 0) {
            this.showToast('Maximum attempts reached');
            return;
        }

        if (!submissionText && this.selectedFiles.length === 0) {
            this.showToast('Please provide submission text or attach files');
            return;
        }

        this.isAssignmentSubmitting = true;

        try {
            const result = await ApiService.submitAssignment(
                this.enrollmentId,
                this.currentLessonId,
                submissionText,
                this.selectedFiles
            );

            if (result.success) {
                this.showToast('Assignment submitted successfully! Waiting for instructor review.');
                this.selectedFiles = [];
                await this.loadAssignmentDetails(this.currentLessonId);
                this.buildAssignmentUI();
            }
        } catch (e) {
            console.error('Assignment submission error:', e);
            this.showToast('Failed to submit assignment');
        } finally {
            this.isAssignmentSubmitting = false;
        }
    }

    async markLessonComplete(isAuto=false) {
        const l=this.getCurrentLesson();
        if(!l||this.isCompleting) return;
        const cl=this.progressData?.completedLessons||[], isDone=cl.includes(l.id);
        const crit=this.parseCompletionCriteria(l);

        if(!isDone&&!isAuto){
            if(crit.criteriaType==='watch_video'&&this.videoWatchPercentage<crit.videoWatchPercentage){this.showToast(`Watch ${crit.videoWatchPercentage}% (current: ${this.videoWatchPercentage}%)`);return;}
            if(crit.criteriaType==='read_article'&&this.articleScrollPercentage<crit.articleScrollPercentage){this.showToast(`Read ${crit.articleScrollPercentage}% (current: ${this.articleScrollPercentage}%)`);return;}
            if(crit.criteriaType==='pass_quiz'&&!this.quizCompleted){this.showToast('Complete quiz first');return;}
            if(crit.criteriaType==='pass_quiz'&&this.quizResultData&&!this.quizResultData.passed){this.showToast(`Need ${crit.quizPassingScore}%`);return;}
            if(crit.criteriaType==='submit_assignment'){this.showToast('Assignment must be approved by instructor');return;}
        }

        this.isCompleting=true;
        this.setCompletionButtonsDisabled(true);
        try {
            const completionData = {
                completed: !isDone,
                auto_completed: isAuto,
                criteria_type: crit.criteriaType,
                watch_percentage: crit.criteriaType === 'watch_video' ? this.videoWatchPercentage : null,
                scroll_percentage: crit.criteriaType === 'read_article' ? this.articleScrollPercentage : null,
                quiz_score: crit.criteriaType === 'pass_quiz' && this.quizResultData ? this.quizResultData.percentage : null
            };
            const res = await ApiService.submitLessonCompletion(this.enrollmentId, l.id, completionData);
            if(res.success || res.completedLessons){
                this.progressData.completedLessons = res.completedLessons || (isDone ? cl.filter(id=>id!==l.id) : [...cl,l.id]);
                this.progressData.completedCount = res.completedCount || this.progressData.completedLessons.length;
                this.progressData.overallProgress = res.overallProgress || Math.round((this.progressData.completedLessons.length/(this.courseData?.totalLessons||12))*100);
                this.showToast(isDone?'Marked incomplete':(isAuto?'Auto-completed!':'Completed!'));
                this.updateProgressUI();

                if (this.checkCourseCompletion()) {
                    this.courseCompleted = true;
                    setTimeout(() => {
                        this.showToast('🎉 Congratulations! Course completed!');
                        this.renderSidebar();
                    }, 1000);
                }

                if (l.type === 'quiz' && this.quizPhase === 'results') {
                    this.renderSidebar();
                    this.setCompleteButtonState(true);
                } else {
                    this.renderLesson();
                    this.renderSidebar();
                    if(!isDone&&!isAuto)setTimeout(()=>{const all=this.getAllLessons();const i=all.findIndex(x=>x.id===l.id);if(i>=0&&i<all.length-1)this.navigateLesson(1);},1500);
                }
            }
        }catch(e){
            this.showToast('Error marking lesson complete');
            console.error('Lesson completion error:', e);
        }finally{
            this.isCompleting=false;
            this.setCompletionButtonsDisabled(false);
        }
    }

    setCompletionButtonsDisabled(d){
        document.querySelectorAll('.mark-complete-btn,.mark-complete-btn-main').forEach(b=>{
            b.disabled=d;
            b.style.opacity=d?'0.5':'1';
            if(d){
                b.setAttribute('data-o',b.innerHTML);
                b.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
            }else{
                const o=b.getAttribute('data-o');
                if(o)b.innerHTML=o;
            }
        });
    }

    async toggleBookmark(){
        const l=this.getCurrentLesson();
        if(!l)return;

        try {
            const result = await ApiService.toggleBookmark(this.enrollmentId, l.id);

            if (result.success) {
                if (result.bookmarked) {
                    this.bookmarkedLessons.add(l.id);
                    this.showToast('Bookmarked!');
                } else {
                    this.bookmarkedLessons.delete(l.id);
                    this.showToast('Bookmark removed');
                }

                if (result.bookmarkedLessons) {
                    this.bookmarkedLessons = new Set(result.bookmarkedLessons);
                }

                if(this.progressData) {
                    this.progressData.bookmarkedLessons = [...this.bookmarkedLessons];
                }

                this.updateBookmarkUI();
                this.renderSidebar();
            }
        } catch(e) {
            console.error('Failed to toggle bookmark:', e);
            this.showToast('Failed to update bookmark');
        }
    }

    updateBookmarkUI(){
        const l=this.getCurrentLesson();
        const b=document.getElementById('bookmarkToggleBtn');
        if(!b)return;
        if(l&&this.bookmarkedLessons.has(l.id)){
            b.innerHTML='<i class="fas fa-bookmark"></i>';
            b.style.color='#F59E0B';
        }else{
            b.innerHTML='<i class="far fa-bookmark"></i>';
            b.style.color='';
        }
    }

    downloadResource(n){this.showToast('Downloading '+n+'...');}
    toggleSidebar(f){this.sidebarOpen=typeof f==='boolean'?f:!this.sidebarOpen;document.getElementById('learnSidebar')?.classList.toggle('open',this.sidebarOpen);}
    handleResponsiveSidebar(){this.toggleSidebar(window.innerWidth>1024);}
    switchTab(tab,skip){
        this.activeTab=tab;
        document.querySelectorAll('.lesson-tab').forEach(t=>t.classList.remove('active'));
        const at=document.querySelector(`.lesson-tab[data-tab="${tab}"]`);
        if(at)at.classList.add('active');
        document.querySelectorAll('.tab-panel').forEach(p=>p.style.display='none');
        const tp=document.getElementById('tab'+tab.charAt(0).toUpperCase()+tab.slice(1));
        if(tp)tp.style.display='block';

        if (tab === 'transcript') {
            const lesson = this.getCurrentLesson();
            if (lesson && lesson.type === 'video') {
                this.renderTranscriptContent(lesson);
            }
        }
    }

    updateProgressUI(){
        if(!this.progressData)return;
        const p=this.progressData.overallProgress||0;
        const c=this.progressData.completedCount||0;
        const t=this.courseData?.totalLessons||12;
        ['navProgressFill','sidebarProgressFill'].forEach(id=>{
            const e=document.getElementById(id);
            if(e)e.style.width=p+'%';
        });
        ['navProgressText','sidebarProgressText'].forEach(id=>{
            const e=document.getElementById(id);
            if(e)e.textContent=p+'% complete';
        });
        const ce=document.getElementById('sidebarProgressCount');
        if(ce)ce.textContent=`${c} / ${t} completed`;

        this.courseCompleted = this.checkCourseCompletion();
    }

    async saveProgressToBackend(){
        if(!this.progressData)return;

        this.saveVideoProgress();
    }

    getFileIconColor(ft){return{image:'#EC4899',pdf:'#EF4444',text:'#10B981',code:'#F59E0B',video:'#3B82F6',audio:'#8B5CF6',other:'#6B7280'}[ft]||'#6B7280';}
    getFileTypeIcon(ft){return{image:'fa-file-image',pdf:'fa-file-pdf',text:'fa-file-alt',code:'fa-file-code',video:'fa-file-video',audio:'fa-file-audio',other:'fa-file'}[ft]||'fa-file';}
    getFileTypeLabel(ft){return{image:'Image File',pdf:'PDF Document',text:'Text File',code:'Code File',video:'Video File',audio:'Audio File',other:'File'}[ft]||'File';}
    getTypeIcon(t){return{video:'<i class="fas fa-play-circle"></i>',article:'<i class="fas fa-file-lines"></i>',quiz:'<i class="fas fa-circle-question"></i>',assignment:'<i class="fas fa-tasks"></i>',file:'<i class="fas fa-file"></i>',live_session:'<i class="fas fa-video"></i>',coding_exercise:'<i class="fas fa-code"></i>'}[t]||'<i class="fas fa-file"></i>';}
    getTypeLabel(t){return{video:'Video',article:'Article',quiz:'Quiz',assignment:'Assignment',file:'File',live_session:'Live Session',coding_exercise:'Coding Exercise'}[t]||this.capitalize(t);}
    getResourceIconClass(t){return{pdf:'fa-file-pdf',code:'fa-file-code',zip:'fa-file-archive',image:'fa-file-image',video:'fa-file-video'}[t]||'fa-file';}
    capitalize(s){return s?s.charAt(0).toUpperCase()+s.slice(1):'';}
    escapeHtml(t){return t?String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'):'';}
    showToast(msg){
        const t=document.createElement('div');
        t.style.cssText='position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#1F2937;color:#FFF;padding:12px 24px;border-radius:8px;font-size:0.85rem;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,0.3);';
        t.textContent=msg;
        document.body.appendChild(t);
        setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity 0.3s';setTimeout(()=>t.remove(),300);},2500);
    }
}

// ============================================
// GLOBAL FUNCTIONS
// ============================================
function toggleSection(h){if(!h)return;h.classList.toggle('open');const l=h.nextElementSibling;if(l)l.style.display=l.style.display==='none'?'':'none';}
function toggleCertificateSection(h){if(!h)return;h.classList.toggle('open');const l=h.nextElementSibling;if(l)l.style.display=l.style.display==='none'?'':'none';}
function navigateToLesson(id){if(window.learningInterface)window.learningInterface.navigateToLessonById(id);}
function showCertificate(){if(window.learningInterface)window.learningInterface.showCertificateModal();}
function closeCertificateModal(){const modal=document.getElementById('certificateModal');if(modal){modal.remove();document.body.style.overflow='';}}
function seekToTranscriptTime(timeString){if(window.learningInterface)window.learningInterface.seekToTranscriptTime(timeString);}
document.addEventListener('DOMContentLoaded',()=>{window.learningInterface=new LearningInterface();});
