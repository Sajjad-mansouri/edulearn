// =============================================================================
// TEMPORARY DUMMY DATA
// -----------------------------------------------------------------------------
// Used only when /api/v1/site-infos/ is unavailable or returns incomplete data.
// All values below are accurate to the current project scope.
// =============================================================================

const dummyData = {
    features: [
        {
            title: 'general',
            items: [
                {
                    title: 'Course Discovery',
                    description:
                        'Browse and filter courses by category, subcategory, level, price, and course metadata.',
                    icon: 'fa-book-open',
                    image: null,
                    color:
                        'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
                },
                {
                    title: 'Authentication & Authorization',
                    description:
                        'JWT authentication with role-based permissions, protected resources, and ownership checks.',
                    icon: 'fa-shield-alt',
                    image: null,
                    color:
                        'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)'
                },
                {
                    title: 'Reviews & Ratings',
                    description:
                        'Enrollment-linked course reviews with visibility controls, ratings, and helpful interactions.',
                    icon: 'fa-star',
                    image: null,
                    color:
                        'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
                },
                {
                    title: 'Certificates',
                    description:
                        'PDF certificate generation with asynchronous processing through Celery.',
                    icon: 'fa-certificate',
                    image: null,
                    color:
                        'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)'
                }
            ]
        },

        {
            title: 'student',
            items: [
                {
                    title: 'Learning Experience',
                    description:
                        'Access lessons, track video progress, resume learning, bookmark lessons, and complete course activities.',
                    icon: 'fa-play-circle',
                    image: null,
                    color:
                        'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)'
                },
                {
                    title: 'Progress Tracking',
                    description:
                        'Track watched duration, completion percentage, resume position, and overall enrollment progress.',
                    icon: 'fa-chart-line',
                    image: null,
                    color:
                        'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)'
                },
                {
                    title: 'Wishlist',
                    description:
                        'Save courses for later with duplicate-prevention constraints and wishlist status management.',
                    icon: 'fa-heart',
                    image: null,
                    color:
                        'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)'
                },
                {
                    title: 'Quizzes & Assignments',
                    description:
                        'Submit assignments, take quizzes, track quiz attempts, and participate in course assessments.',
                    icon: 'fa-tasks',
                    image: null,
                    color:
                        'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)'
                }
            ]
        },

        {
            title: 'instructor',
            items: [
                {
                    title: 'Course Management',
                    description:
                        'Manage the course lifecycle from creation and editing through submission and publication.',
                    icon: 'fa-chalkboard',
                    image: null,
                    color:
                        'linear-gradient(135deg, #6366f1 0%, #818cf8 100%)'
                },
                {
                    title: 'Analytics & Revenue',
                    description:
                        'Analyze course performance, student progress, ratings, revenue, and transaction history.',
                    icon: 'fa-chart-bar',
                    image: null,
                    color:
                        'linear-gradient(135deg, #f97316 0%, #fb923c 100%)'
                },
                {
                    title: 'Student Management',
                    description:
                        'View enrolled students, learning progress, activity, status, and course-related performance.',
                    icon: 'fa-user-graduate',
                    image: null,
                    color:
                        'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)'
                },
                {
                    title: 'Assignment Grading',
                    description:
                        'Review, download, bulk-download, and grade student assignment submissions with authorization checks.',
                    icon: 'fa-file-upload',
                    image: null,
                    color:
                        'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
                }
            ]
        }
    ],

    highlights: [
        {
            title: 'JWT Authentication & Authorization',
            description:
                'JWT-based authentication combined with role-based permissions, protected resources, and ownership validation.',
            icon: 'fa-shield-alt',
            color: '#4f46e5',
            endpoints: [
                'POST /token/',
                'POST /token/refresh/',
                'POST /token/verify/',
                'GET /current-user/'
            ]
        },

        {
            title: 'Course Lifecycle Management',
            description:
                'Manage courses through creation, editing, submission, review-related states, and publication with state-dependent business rules.',
            icon: 'fa-book',
            color: '#059669',
            endpoints: [
                'POST /courses/create/<course_status>/',
                'POST /courses/<course_id>/submit/',
                'POST /courses/<course_id>/publish/',
                'GET /courses/'
            ]
        },

        {
            title: 'Stripe Payment Integration',
            description:
                'Stripe Checkout integration with payment state management, webhook processing, and transaction-safe database updates.',
            icon: 'fa-credit-card',
            color: '#dc2626',
            endpoints: [
                'POST /enrollments/<enrollment_id>/checkout/',
                'POST /webhooks/stripe/'
            ]
        },

        {
            title: 'Instructor Analytics',
            description:
                'Instructor-scoped analytics covering course performance, student progress, ratings, revenue, and transaction history.',
            icon: 'fa-chart-line',
            color: '#f59e0b',
            endpoints: [
                'GET /analytics/',
                'GET /analytics/courses/',
                'GET /revenue/',
                'GET /transactions/'
            ]
        },

        {
            title: 'Celery Background Processing',
            description:
                'Asynchronous processing for background operations with automatic retries, exception handling, and database transactions.',
            icon: 'fa-cogs',
            color: '#8b5cf6',
            endpoints: [
                'Certificate generation tasks',
                'Retryable background tasks'
            ]
        },

        {
            title: 'Certificate Generation',
            description:
                'Generate and persist PDF certificates for completed courses, with background processing through Celery.',
            icon: 'fa-certificate',
            color: '#06b6d4',
            endpoints: [
                'GET /certificates/',
                'GET /certificate/<id>/download/'
            ]
        }
    ],

    contact: {
        name: 'Your Name',
        title: 'Django Backend Developer',
        description:
            'Backend-focused Django developer building maintainable, well-tested applications with clear domain modeling, robust business rules, secure APIs, and reliable integrations.',
        email: 'your.email@example.com',
        social_links: [
            {
                platform: 'GitHub',
                url: 'https://github.com/yourusername',
                icon: 'fab fa-github',
                username: 'github.com/yourusername'
            },
            {
                platform: 'LinkedIn',
                url: 'https://linkedin.com/in/yourusername',
                icon: 'fab fa-linkedin',
                username: 'linkedin.com/in/yourusername'
            }
        ]
    },

    statistics: {
        api_endpoints: '80+',
        automated_tests: '6,271+',
        django_apps: 7,
        major_features: '10+'
    }
};


// =============================================================================
// State
// =============================================================================

let featureData = cloneData(dummyData.features);
let contactData = transformContactData(dummyData.contact);
let highlightData = cloneData(dummyData.highlights);

let apiEndpointsCount = dummyData.statistics.api_endpoints;
let testsCount = dummyData.statistics.automated_tests;
let djangoAppsCount = dummyData.statistics.django_apps;
let majorFeaturesCount = dummyData.statistics.major_features;

let currentTab = 'general';


// =============================================================================
// Utilities
// =============================================================================

function cloneData(data) {
    return JSON.parse(JSON.stringify(data));
}


function getDefaultCardColor() {
    return 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)';
}


function getEndpointText(endpoint) {
    if (typeof endpoint === 'string') {
        return endpoint.trim();
    }

    if (endpoint && typeof endpoint === 'object') {
        return (
            endpoint.end_point ||
            endpoint.endpoint ||
            endpoint.path ||
            endpoint.url ||
            ''
        ).trim();
    }

    return '';
}


// =============================================================================
// Transform helpers
// -----------------------------------------------------------------------------
// API data → frontend internal format
// =============================================================================

function transformFeaturesData(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(group => ({
        title: group.title || 'general',

        items: Array.isArray(group.items)
            ? group.items.map(item => ({
                  title: item.title || 'Untitled',
                  description: item.description || '',
                  icon: item.icon || 'fa-star',
                  image: item.image || null,
                  color: item.color || getDefaultCardColor()
              }))
            : []
    }));
}


function transformHighlightsData(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map(highlight => ({
        title: highlight.title || 'Untitled',
        description: highlight.description || '',
        icon: highlight.icon || 'fa-star',
        color: highlight.color || '#4f46e5',

        endpoints: Array.isArray(highlight.endpoints)
            ? highlight.endpoints
                  .map(getEndpointText)
                  .filter(Boolean)
            : []
    }));
}


function transformContactData(data) {
    if (!data || typeof data !== 'object') {
        return {
            name: dummyData.contact.name,
            title: dummyData.contact.title,
            description: dummyData.contact.description,
            email: dummyData.contact.email,
            socialLinks: cloneData(dummyData.contact.social_links)
        };
    }

    const rawSocialLinks =
        Array.isArray(data.social_links)
            ? data.social_links
            : Array.isArray(data.socialLinks)
              ? data.socialLinks
              : [];

    const normalizedSocialLinks =
        rawSocialLinks
            .map(link => {
                if (!link || typeof link !== 'object') {
                    return null;
                }

                const platform =
                    link.platform ||
                    link.name ||
                    link.title ||
                    '';

                const url =
                    link.url ||
                    link.href ||
                    link.link ||
                    '';

                const icon =
                    link.icon ||
                    'fas fa-link';

                const username =
                    link.username ||
                    link.label ||
                    link.display_name ||
                    link.displayName ||
                    '';

                return {
                    platform,
                    url,
                    icon,
                    username
                };
            })
            .filter(link => link && link.url);

    const socialLinks =
        normalizedSocialLinks.length > 0
            ? normalizedSocialLinks
            : cloneData(dummyData.contact.social_links);

    return {
        name:
            data.name ||
            dummyData.contact.name,

        title:
            data.title ||
            dummyData.contact.title,

        description:
            data.description ||
            dummyData.contact.description,

        email:
            data.email ||
            dummyData.contact.email,

        socialLinks
    };
}

function transformStatisticsData(data) {
    if (!data || typeof data !== 'object') {
        return {
            apiEndpoints: dummyData.statistics.api_endpoints,
            automatedTests: dummyData.statistics.automated_tests,
            djangoApps: dummyData.statistics.django_apps,
            majorFeatures: dummyData.statistics.major_features
        };
    }

    return {
        apiEndpoints:
            data.api_endpoints ??
            data.apiEndpoints ??
            dummyData.statistics.api_endpoints,

        automatedTests:
            data.automated_tests ??
            data.automatedTests ??
            dummyData.statistics.automated_tests,

        djangoApps:
            data.django_apps ??
            data.djangoApps ??
            dummyData.statistics.django_apps,

        majorFeatures:
            data.major_features ??
            data.majorFeatures ??
            dummyData.statistics.major_features
    };
}


// =============================================================================
// Backend data validation
// =============================================================================

function hasCompleteSiteInfo(data) {
    if (!data || typeof data !== 'object') {
        return false;
    }

    return (
        Array.isArray(data.features) &&
        Array.isArray(data.highlights) &&
        data.contact &&
        typeof data.contact === 'object' &&
        data.statistics &&
        typeof data.statistics === 'object'
    );
}


// =============================================================================
// Fetch from backend
// -----------------------------------------------------------------------------
// Backend is preferred.
// Dummy data is used when the endpoint fails or returns incomplete data.
// =============================================================================

async function fetchData() {
    try {
        const origin = window.location.origin;
        const url = `${origin}/api/v1/site-info/`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                Accept: 'application/json'
            }
        });
        if (!response.ok) {
            console.warn(
                `site-info endpoint returned HTTP ${response.status}. ` +
                'Using temporary dummy data.'
            );

            useDummyData();
            return;
        }

        const data = await response.json();
        console.log(data)

        console.log('Backend site-info data:', data);

        if (!hasCompleteSiteInfo(data)) {
            console.warn(
                'Backend site-info response is incomplete. ' +
                'Using temporary dummy data.'
            );

            useDummyData();
            return;
        }

        featureData =
            transformFeaturesData(
                data.features
            );

        highlightData =
            transformHighlightsData(
                data.highlights
            );

        contactData =
            transformContactData(
                data.contact
            );

        const statistics =
            transformStatisticsData(
                data.statistics
            );

        apiEndpointsCount =
            statistics.apiEndpoints;

        testsCount =
            statistics.automatedTests;

        djangoAppsCount =
            statistics.djangoApps;

        majorFeaturesCount =
            statistics.majorFeatures;

        console.log(
            'Normalized contact data:',
            contactData
        );

        console.log(
            'Using live backend data'
        );
    } catch (error) {
        console.error(
            'Error fetching site-info:',
            error
        );

        console.warn(
            'Falling back to temporary dummy data.'
        );

        useDummyData();
    } finally {
        renderHeroStats();
        renderFeatureTabs();
        renderHighlights();
        renderContactInfo();
        renderFooter();

        requestAnimationFrame(() => {
            updateAllScrollArrows();
        });
    }
}


// =============================================================================
// Dummy data fallback
// =============================================================================

function useDummyData() {
    featureData =
        cloneData(dummyData.features);

    contactData =
        transformContactData(dummyData.contact);

    highlightData =
        cloneData(dummyData.highlights);

    apiEndpointsCount =
        dummyData.statistics.api_endpoints;

    testsCount =
        dummyData.statistics.automated_tests;

    djangoAppsCount =
        dummyData.statistics.django_apps;

    majorFeaturesCount =
        dummyData.statistics.major_features;
}


// =============================================================================
// Hero statistics
// =============================================================================

function renderHeroStats() {
    const heroStats =
        document.querySelector('.hero-stats');

    if (!heroStats) {
        return;
    }

    heroStats.innerHTML = `
        <div class="stat-item">
            <h3>${apiEndpointsCount}</h3>
            <p>API Endpoints</p>
        </div>

        <div class="stat-item">
            <h3>${testsCount}</h3>
            <p>Automated Tests</p>
        </div>

    `;
}


// =============================================================================
// Feature tabs
// =============================================================================

function renderFeatureTabs() {
    const tabContainer =
        document.getElementById(
            'tabContainer'
        );

    const tabContents =
        document.getElementById(
            'tabContents'
        );

    if (!tabContainer || !tabContents) {
        return;
    }

    tabContainer.innerHTML = '';
    tabContents.innerHTML = '';

    let tabs = [];

    if (Array.isArray(featureData)) {
        tabs = featureData.map(group => ({
            id: group.title || 'general',

            label: group.title
                ? group.title.charAt(0).toUpperCase() +
                  group.title.slice(1)
                : 'General',

            icon: getTabIcon(group.title),

            items: Array.isArray(group.items)
                ? group.items
                : []
        }));
    } else if (
        featureData &&
        typeof featureData === 'object'
    ) {
        const tabNames =
            Object.keys(featureData);

        tabs = tabNames.map(name => ({
            id: name,

            label:
                name.charAt(0).toUpperCase() +
                name.slice(1),

            icon: getTabIcon(name),

            items: Array.isArray(featureData[name])
                ? featureData[name]
                : []
        }));
    }

    if (tabs.length === 0) {
        tabs = [
            {
                id: 'general',
                label: 'General',
                icon: 'fa-globe',
                items: []
            },
            {
                id: 'student',
                label: 'Student',
                icon: 'fa-user-graduate',
                items: []
            },
            {
                id: 'instructor',
                label: 'Instructor',
                icon: 'fa-chalkboard-teacher',
                items: []
            }
        ];
    }

    tabs.forEach((tab, index) => {
        const button =
            document.createElement('button');

        button.type = 'button';

        button.className =
            `tab-button ${index === 0 ? 'active' : ''}`;

        button.setAttribute(
            'data-tab',
            tab.id
        );

        button.innerHTML = `
            <i class="fas ${tab.icon}"></i>
            ${tab.label}
        `;

        button.addEventListener(
            'click',
            () => switchTab(tab.id)
        );

        tabContainer.appendChild(
            button
        );
    });

    tabs.forEach((tab, index) => {
        const content =
            document.createElement('div');

        content.className =
            `tab-content ${index === 0 ? 'active' : ''}`;

        content.id = tab.id;

        const scrollContainer =
            document.createElement('div');

        scrollContainer.className =
            'scroll-container';

        const leftArrow =
            document.createElement('button');

        leftArrow.type = 'button';

        leftArrow.className =
            'scroll-arrow scroll-arrow-left';

        leftArrow.setAttribute(
            'aria-label',
            'Scroll left'
        );

        leftArrow.innerHTML =
            '<i class="fas fa-chevron-left"></i>';

        leftArrow.addEventListener(
            'click',
            () => scrollCards(tab.id, -1)
        );

        const grid =
            document.createElement('div');

        grid.className =
            'role-grid';

        grid.id =
            `${tab.id}-grid`;

        (tab.items || []).forEach(
            (card, cardIndex) => {
                grid.appendChild(
                    createFeatureCard(
                        card,
                        tab.id,
                        cardIndex
                    )
                );
            }
        );

        /*
         * Update arrow visibility whenever
         * the user manually scrolls the cards.
         */
        grid.addEventListener(
            'scroll',
            () => {
                updateScrollArrows(grid);
            }
        );

        const rightArrow =
            document.createElement('button');

        rightArrow.type = 'button';

        rightArrow.className =
            'scroll-arrow scroll-arrow-right';

        rightArrow.setAttribute(
            'aria-label',
            'Scroll right'
        );

        rightArrow.innerHTML =
            '<i class="fas fa-chevron-right"></i>';

        rightArrow.addEventListener(
            'click',
            () => scrollCards(tab.id, 1)
        );

        scrollContainer.appendChild(
            leftArrow
        );

        scrollContainer.appendChild(
            grid
        );

        scrollContainer.appendChild(
            rightArrow
        );

        content.appendChild(
            scrollContainer
        );

        tabContents.appendChild(
            content
        );
    });

    if (tabs.length > 0) {
        currentTab = tabs[0].id;
    }

    /*
     * Wait until the browser has laid out the grids
     * before determining whether scrolling is possible.
     */
    requestAnimationFrame(() => {
        updateAllScrollArrows();
    });
}


function getTabIcon(tabName) {
    const icons = {
        general: 'fa-globe',
        student: 'fa-user-graduate',
        instructor: 'fa-chalkboard-teacher'
    };

    return icons[tabName] || 'fa-globe';
}


// =============================================================================
// Feature cards
// =============================================================================

function createFeatureCard(
    card,
    tabId,
    index
) {
    const cardElement =
        document.createElement('div');

    cardElement.className =
        'role-card';

    cardElement.setAttribute(
        'role',
        'button'
    );

    cardElement.setAttribute(
        'tabindex',
        '0'
    );

    cardElement.addEventListener(
        'click',
        () => openModal(
            tabId,
            index,
            card
        )
    );

    cardElement.addEventListener(
        'keydown',
        event => {
            if (
                event.key === 'Enter' ||
                event.key === ' '
            ) {
                event.preventDefault();

                openModal(
                    tabId,
                    index,
                    card
                );
            }
        }
    );

    const imageContainer =
        document.createElement('div');

    imageContainer.className =
        'role-card-image';

    if (card.image) {
        const img =
            document.createElement('img');

        img.src = card.image;

        img.alt =
            card.title || 'Feature image';

        img.onerror = function () {
            this.remove();

            imageContainer.style.background =
                card.color ||
                getDefaultCardColor();

            const icon =
                document.createElement('i');

            icon.className =
                `fas ${card.icon || 'fa-star'}`;

            imageContainer.appendChild(
                icon
            );
        };

        imageContainer.appendChild(img);
    } else {
        imageContainer.style.background =
            card.color ||
            getDefaultCardColor();

        const icon =
            document.createElement('i');

        icon.className =
            `fas ${card.icon || 'fa-star'}`;

        imageContainer.appendChild(
            icon
        );
    }

    const content =
        document.createElement('div');

    content.className =
        'role-card-content';

    const title =
        document.createElement('h3');

    title.textContent =
        card.title || 'Untitled';

    const description =
        document.createElement('p');

    description.textContent =
        card.description ||
        'No description available';

    content.appendChild(title);
    content.appendChild(description);

    cardElement.appendChild(
        imageContainer
    );

    cardElement.appendChild(
        content
    );

    return cardElement;
}


// =============================================================================
// Tab switching
// =============================================================================

function switchTab(tabId) {
    currentTab = tabId;

    document
        .querySelectorAll('.tab-button')
        .forEach(button => {
            button.classList.toggle(
                'active',
                button.getAttribute(
                    'data-tab'
                ) === tabId
            );
        });

    document
        .querySelectorAll('.tab-content')
        .forEach(content => {
            content.classList.toggle(
                'active',
                content.id === tabId
            );
        });

    requestAnimationFrame(() => {
        const grid =
            document.getElementById(
                `${tabId}-grid`
            );

        updateScrollArrows(grid);
    });
}


// =============================================================================
// Horizontal card scrolling
// =============================================================================

function updateScrollArrows(grid) {
    if (!grid) {
        return;
    }

    const scrollContainer =
        grid.parentElement;

    if (!scrollContainer) {
        return;
    }

    const leftArrow =
        scrollContainer.querySelector(
            '.scroll-arrow-left'
        );

    const rightArrow =
        scrollContainer.querySelector(
            '.scroll-arrow-right'
        );

    if (!leftArrow || !rightArrow) {
        return;
    }

    const canScrollLeft =
        grid.scrollLeft > 1;

    const canScrollRight =
        grid.scrollLeft +
            grid.clientWidth <
        grid.scrollWidth - 1;

    leftArrow.style.display =
        canScrollLeft
            ? 'flex'
            : 'none';

    rightArrow.style.display =
        canScrollRight
            ? 'flex'
            : 'none';

    leftArrow.disabled =
        !canScrollLeft;

    rightArrow.disabled =
        !canScrollRight;

    leftArrow.setAttribute(
        'aria-hidden',
        String(!canScrollLeft)
    );

    rightArrow.setAttribute(
        'aria-hidden',
        String(!canScrollRight)
    );
}


function updateAllScrollArrows() {
    document
        .querySelectorAll('.role-grid')
        .forEach(grid => {
            updateScrollArrows(grid);
        });
}


function scrollCards(
    tabId,
    direction
) {
    const grid =
        document.getElementById(
            `${tabId}-grid`
        );

    if (!grid) {
        return;
    }

    const scrollAmount =
        Math.max(
            grid.clientWidth * 0.75,
            300
        );

    grid.scrollBy({
        left:
            scrollAmount * direction,
        behavior: 'smooth'
    });

    /*
     * Update immediately and again after
     * smooth scrolling has progressed.
     */
    updateScrollArrows(grid);

    setTimeout(() => {
        updateScrollArrows(grid);
    }, 350);
}


// =============================================================================
// Highlights
// =============================================================================

function renderHighlights() {
    const highlightsGrid =
        document.getElementById(
            'highlightsGrid'
        );

    if (!highlightsGrid) {
        return;
    }

    highlightsGrid.innerHTML = '';

    highlightData.forEach(highlight => {
        const card =
            document.createElement('div');

        card.className =
            'highlight-card';

        const icon =
            document.createElement('div');

        icon.className =
            'highlight-icon';

        const highlightColor =
            highlight.color || '#4f46e5';

        icon.style.background =
            `${highlightColor}20`;

        icon.style.color =
            highlightColor;

        icon.innerHTML =
            `<i class="fas ${highlight.icon || 'fa-star'}"></i>`;

        const title =
            document.createElement('h3');

        title.textContent =
            highlight.title || 'Untitled';

        const description =
            document.createElement('p');

        description.textContent =
            highlight.description || '';

        const endpointsDiv =
            document.createElement('div');

        endpointsDiv.className =
            'highlight-endpoints';

        const endpoints =
            Array.isArray(highlight.endpoints)
                ? highlight.endpoints
                : [];

        endpoints.forEach(endpoint => {
            const endpointText =
                getEndpointText(endpoint);

            if (!endpointText) {
                return;
            }

            const tag =
                document.createElement('span');

            tag.className =
                'endpoint-tag';

            tag.textContent =
                endpointText;

            endpointsDiv.appendChild(
                tag
            );
        });

        card.appendChild(icon);
        card.appendChild(title);
        card.appendChild(description);

        if (endpoints.length > 0) {
            card.appendChild(
                endpointsDiv
            );
        }

        highlightsGrid.appendChild(card);
    });
}


// =============================================================================
// Contact information
// =============================================================================

function renderContactInfo() {
    const contactInfo =
        document.getElementById(
            'contactInfo'
        );

    if (!contactInfo) {
        return;
    }

    contactInfo.innerHTML = '';

    const heading =
        document.createElement('h3');

    heading.textContent =
        "Let's Connect!";

    const description =
        document.createElement('p');

    description.textContent =
        contactData.description ||
        'Feel free to reach out about backend engineering, Django/DRF projects or collaboration.';

    const socialLinks =
        document.createElement('div');

    socialLinks.className =
        'social-links';

    if (contactData.email) {
        const emailLink =
            document.createElement('a');

        emailLink.href =
            `mailto:${contactData.email}`;

        emailLink.className =
            'social-link';

        const emailIcon =
            document.createElement('i');

        emailIcon.className =
            'fas fa-envelope';

        const emailContent =
            document.createElement('div');

        const emailTitle =
            document.createElement('strong');

        emailTitle.textContent =
            'Email';

        const emailAddress =
            document.createElement('p');

        emailAddress.style.margin =
            '0';

        emailAddress.style.fontSize =
            '0.9rem';

        emailAddress.textContent =
            contactData.email;

        emailContent.appendChild(
            emailTitle
        );

        emailContent.appendChild(
            emailAddress
        );

        emailLink.appendChild(
            emailIcon
        );

        emailLink.appendChild(
            emailContent
        );

        socialLinks.appendChild(
            emailLink
        );
    }

    const links =
        contactData.socialLinks ||
        contactData.social_links ||
        [];

    links.forEach(link => {
        if (
            !link ||
            !link.url
        ) {
            return;
        }

        const socialLink =
            document.createElement('a');

        socialLink.href =
            link.url;

        socialLink.target =
            '_blank';

        socialLink.rel =
            'noopener noreferrer';

        socialLink.className =
            'social-link';

        const icon =
            document.createElement('i');

        icon.className =
            link.icon ||
            'fas fa-link';

        const content =
            document.createElement('div');

        const platform =
            document.createElement('strong');

        platform.textContent =
            link.platform ||
            link.name ||
            'Link';

        const username =
            document.createElement('p');

        username.style.margin =
            '0';

        username.style.fontSize =
            '0.9rem';

        username.textContent =
            link.username ||
            link.url;

        content.appendChild(
            platform
        );

        content.appendChild(
            username
        );

        socialLink.appendChild(
            icon
        );

        socialLink.appendChild(
            content
        );

        socialLinks.appendChild(
            socialLink
        );
    });

    contactInfo.appendChild(
        heading
    );

    contactInfo.appendChild(
        description
    );

    contactInfo.appendChild(
        socialLinks
    );
}


// =============================================================================
// Footer
// =============================================================================

function renderFooter() {
    const footerLinks =
        document.getElementById(
            'footerLinks'
        );

    if (!footerLinks) {
        return;
    }

    footerLinks.innerHTML = '';

    const links = [
        {
            text: 'Sign Up',
            url: '/account/auth/register/student/',
            icon: 'fas fa-user-plus'
        },
        {
            text: 'Login',
            url: '/account/auth/login/',
            icon: 'fas fa-sign-in-alt'
        },
        {
            text: 'Contact',
            url: '#contact',
            icon: 'fas fa-envelope'
        }
    ];

    const contactLinks =
        contactData.socialLinks ||
        contactData.social_links ||
        [];

    contactLinks.forEach(link => {
        if (!link || !link.url) {
            return;
        }

        links.push({
            text:
                link.platform ||
                link.name ||
                'Link',

            url:
                link.url,

            icon:
                link.icon ||
                'fas fa-link'
        });
    });

    links.forEach(link => {
        const anchor =
            document.createElement('a');

        anchor.href =
            link.url;

        if (
            link.url.startsWith('http')
        ) {
            anchor.target =
                '_blank';

            anchor.rel =
                'noopener noreferrer';
        }

        const iconClass =
            link.icon ||
            'fas fa-link';

        anchor.innerHTML =
            `<i class="${iconClass}"></i> ${link.text}`;

        footerLinks.appendChild(
            anchor
        );
    });
}


// =============================================================================
// Modal
// =============================================================================

function openModal(
    tabId,
    cardIndex,
    card
) {
    const modal =
        document.getElementById(
            'imageModal'
        );

    const modalImage =
        document.getElementById(
            'modalImage'
        );

    const modalTitle =
        document.getElementById(
            'modalTitle'
        );

    const modalDescription =
        document.getElementById(
            'modalDescription'
        );

    if (
        !modal ||
        !modalImage ||
        !modalTitle ||
        !modalDescription
    ) {
        return;
    }

    modalImage.innerHTML = '';
    modalImage.style.background = '';

    if (card.image) {
        const img =
            document.createElement('img');

        img.src =
            card.image;

        img.alt =
            card.title || 'Feature image';

        img.onerror = function () {
            this.remove();

            modalImage.style.background =
                card.color ||
                getDefaultCardColor();

            modalImage.innerHTML =
                `<i class="fas ${card.icon || 'fa-star'}"></i>`;
        };

        modalImage.appendChild(img);
    } else {
        modalImage.style.background =
            card.color ||
            getDefaultCardColor();

        modalImage.innerHTML =
            `<i class="fas ${card.icon || 'fa-star'}"></i>`;
    }

    modalTitle.textContent =
        card.title || 'Untitled';

    modalDescription.textContent =
        card.description ||
        'No description available';

    modal.classList.add(
        'active'
    );

    document.body.style.overflow =
        'hidden';
}


function closeModal() {
    const modal =
        document.getElementById(
            'imageModal'
        );

    if (!modal) {
        return;
    }

    modal.classList.remove(
        'active'
    );

    document.body.style.overflow =
        'auto';
}


// =============================================================================
// Contact form
// =============================================================================

async function submitContactForm(
    formData
) {
    const formFeedback =
        document.getElementById(
            'formFeedback'
        );

    const submitBtn =
        document.getElementById(
            'submitBtn'
        );

    const contactForm =
        document.getElementById(
            'contactForm'
        );

    if (submitBtn) {
        submitBtn.disabled =
            true;

        submitBtn.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Sending...';
    }

    if (formFeedback) {
        formFeedback.style.display =
            'none';

        formFeedback.className =
            'form-feedback';
    }

    try {
        const origin =
            window.location.origin;

        const url =
            `${origin}/api/v1/message/`;

        const response =
            await fetch(url, {
                method: 'POST',

                headers: {
                    'Content-Type':
                        'application/json',
                    Accept:
                        'application/json'
                },

                body:
                    JSON.stringify(
                        formData
                    )
            });

        let data = {};

        try {
            data =
                await response.json();
        } catch {
            data = {};
        }

        if (response.ok) {
            if (formFeedback) {
                formFeedback.textContent =
                    "✅ Message sent successfully! I'll get back to you soon.";

                formFeedback.style.color =
                    'var(--color-success)';

                formFeedback.className =
                    'form-feedback show success';

                formFeedback.style.display =
                    'block';
            }

            if (contactForm) {
                contactForm.reset();
            }
        } else {
            if (formFeedback) {
                formFeedback.textContent =
                    data.detail ||
                    data.message ||
                    'Something went wrong. Please try again.';

                formFeedback.style.color =
                    'var(--color-error)';

                formFeedback.className =
                    'form-feedback show error';

                formFeedback.style.display =
                    'block';
            }
        }
    } catch (error) {
        console.error(
            'Error submitting form:',
            error
        );

        if (formFeedback) {
            formFeedback.textContent =
                '❌ Failed to send. Please try again later.';

            formFeedback.style.color =
                'var(--color-error)';

            formFeedback.className =
                'form-feedback show error';

            formFeedback.style.display =
                'block';
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled =
                false;

            submitBtn.innerHTML =
                '<i class="fas fa-paper-plane"></i> Send Message';
        }
    }

    return true;
}


// =============================================================================
// Cookie utility
// =============================================================================

function getCookie(name) {
    let cookieValue = null;

    if (
        document.cookie &&
        document.cookie !== ''
    ) {
        const cookies =
            document.cookie.split(';');

        for (
            let i = 0;
            i < cookies.length;
            i++
        ) {
            const cookie =
                cookies[i].trim();

            if (
                cookie.substring(
                    0,
                    name.length + 1
                ) === `${name}=`
            ) {
                cookieValue =
                    decodeURIComponent(
                        cookie.substring(
                            name.length + 1
                        )
                    );

                break;
            }
        }
    }

    return cookieValue;
}


// =============================================================================
// Hamburger menu
// =============================================================================

function initHamburgerMenu() {
    const hamburgerBtn =
        document.getElementById(
            'hamburgerBtn'
        );

    const navbarMenu =
        document.getElementById(
            'navbarMenu'
        );

    if (
        !hamburgerBtn ||
        !navbarMenu
    ) {
        return;
    }

    hamburgerBtn.addEventListener(
        'click',
        function (event) {
            event.preventDefault();
            event.stopPropagation();

            hamburgerBtn.classList.toggle(
                'active'
            );

            navbarMenu.classList.toggle(
                'active'
            );
        }
    );

    navbarMenu
        .querySelectorAll('a')
        .forEach(link => {
            link.addEventListener(
                'click',
                () => {
                    hamburgerBtn.classList.remove(
                        'active'
                    );

                    navbarMenu.classList.remove(
                        'active'
                    );
                }
            );
        });

    document.addEventListener(
        'click',
        function (event) {
            if (
                !navbarMenu.contains(
                    event.target
                ) &&
                !hamburgerBtn.contains(
                    event.target
                )
            ) {
                hamburgerBtn.classList.remove(
                    'active'
                );

                navbarMenu.classList.remove(
                    'active'
                );
            }
        }
    );

    window.addEventListener(
        'resize',
        function () {
            if (window.innerWidth > 768) {
                hamburgerBtn.classList.remove(
                    'active'
                );

                navbarMenu.classList.remove(
                    'active'
                );
            }
        }
    );
}


// =============================================================================
// Initialize
// =============================================================================

document.addEventListener(
    'DOMContentLoaded',
    () => {
        fetchData();

        initHamburgerMenu();

        // ---------------------------------------------------------------------
        // Modal
        // ---------------------------------------------------------------------

        const modal =
            document.getElementById(
                'imageModal'
            );

        if (modal) {
            modal.addEventListener(
                'click',
                function (event) {
                    if (
                        event.target === this
                    ) {
                        closeModal();
                    }
                }
            );
        }

        document.addEventListener(
            'keydown',
            function (event) {
                if (
                    event.key === 'Escape'
                ) {
                    closeModal();
                }
            }
        );

        // ---------------------------------------------------------------------
        // Contact form
        // ---------------------------------------------------------------------

        const contactForm =
            document.getElementById(
                'contactForm'
            );

        if (contactForm) {
            contactForm.addEventListener(
                'submit',
                async function (event) {
                    event.preventDefault();

                    const nameInput =
                        document.getElementById(
                            'name'
                        );

                    const emailInput =
                        document.getElementById(
                            'email'
                        );

                    const subjectInput =
                        document.getElementById(
                            'subject'
                        );

                    const messageInput =
                        document.getElementById(
                            'message'
                        );

                    const formData = {
                        name:
                            nameInput
                                ? nameInput.value
                                : '',

                        email:
                            emailInput
                                ? emailInput.value
                                : '',

                        subject:
                            subjectInput
                                ? subjectInput.value
                                : '',

                        message:
                            messageInput
                                ? messageInput.value
                                : ''
                    };

                    await submitContactForm(
                        formData
                    );
                }
            );
        }

        // ---------------------------------------------------------------------
        // Smooth scrolling
        // ---------------------------------------------------------------------

        document
            .querySelectorAll(
                'a[href^="#"]'
            )
            .forEach(anchor => {
                anchor.addEventListener(
                    'click',
                    function (event) {
                        const targetId =
                            this.getAttribute(
                                'href'
                            );

                        if (
                            !targetId ||
                            targetId === '#'
                        ) {
                            return;
                        }

                        const target =
                            document.querySelector(
                                targetId
                            );

                        if (!target) {
                            return;
                        }

                        event.preventDefault();

                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                );
            });

        // ---------------------------------------------------------------------
        // Footer year
        // ---------------------------------------------------------------------

        const year =
            new Date().getFullYear();

        const footerText =
            document.getElementById(
                'footerText'
            );

        if (footerText) {
            footerText.textContent +=
                ` © ${year}`;
        }

        // ---------------------------------------------------------------------
        // Scroll arrows
        // ---------------------------------------------------------------------

        window.addEventListener(
            'resize',
            () => {
                requestAnimationFrame(() => {
                    updateAllScrollArrows();
                });
            }
        );
    }
);
