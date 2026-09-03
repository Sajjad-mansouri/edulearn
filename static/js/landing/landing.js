

// Curated dummy data - Only showing key features, not all endpoints
const dummyData = {
    features: [
        {
            title: 'general',
            items: [
                { title: 'Course Catalog', description: 'Browse courses with advanced filtering and categories', icon: 'fa-book-open', image: null, color: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)' },
                { title: 'Smart Search', description: 'Powerful search with metadata-driven discovery', icon: 'fa-search', image: null, color: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)' },
                { title: 'Reviews & Ratings', description: 'Community-driven feedback system', icon: 'fa-star', image: null, color: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)' },
                { title: 'Certification', description: 'Earn certificates upon completion', icon: 'fa-certificate', image: null, color: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)' }
            ]
        },
        {
            title: 'student',
            items: [
                { title: 'Interactive Learning', description: 'Video lessons, quizzes, and assignments', icon: 'fa-play-circle', image: null, color: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)' },
                { title: 'Progress Tracking', description: 'Monitor your learning journey', icon: 'fa-chart-line', image: null, color: 'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)' },
                { title: 'Wishlist', description: 'Save courses for later', icon: 'fa-heart', image: null, color: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)' },
                { title: 'Assignments', description: 'Submit work and get feedback', icon: 'fa-tasks', image: null, color: 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)' }
            ]
        },
        {
            title: 'instructor',
            items: [
                { title: 'Course Builder', description: 'Create and manage courses', icon: 'fa-chalkboard', image: null, color: 'linear-gradient(135deg, #6366f1 0%, #818cf8 100%)' },
                { title: 'Analytics', description: 'Track performance and revenue', icon: 'fa-chart-bar', image: null, color: 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)' },
                { title: 'Student Management', description: 'Track progress and enrollments', icon: 'fa-user-graduate', image: null, color: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)' },
                { title: 'Revenue Tracking', description: 'Monitor earnings and transactions', icon: 'fa-money-bill-wave', image: null, color: 'linear-gradient(135deg, #06b6d4 0%, #67e8f9 100%)' }
            ]
        }
    ],
    highlights: [
        {
            title: 'JWT Authentication',
            description: 'Secure token-based authentication with refresh tokens and role-based access control',
            icon: 'fa-shield-alt',
            color: '#4f46e5',
            endpoints: [
                { end_point: '/api/v1/account/auth/token/' },
                { end_point: '/api/v1/account/auth/refresh/' }
            ]
        },
        {
            title: 'Course Management',
            description: 'Full CRUD operations for courses, lessons, and curriculum',
            icon: 'fa-book',
            color: '#059669',
            endpoints: [
                { end_point: '/api/v1/courses/' },
                { end_point: '/api/v1/instructor/courses/' }
            ]
        },
        {
            title: 'Payment Processing',
            description: 'Stripe integration for secure payment processing and webhooks',
            icon: 'fa-credit-card',
            color: '#dc2626',
            endpoints: [
                { end_point: '/api/v1/payment/checkout/' }
            ]
        },
        {
            title: 'Real-time Analytics',
            description: 'Comprehensive analytics for student performance and revenue',
            icon: 'fa-chart-line',
            color: '#f59e0b',
            endpoints: [
                { end_point: '/api/v1/instructor/analytics/' }
            ]
        },
        {
            title: 'File Management',
            description: 'Assignment submissions with bulk download capabilities',
            icon: 'fa-file-upload',
            color: '#8b5cf6',
            endpoints: [
                { end_point: '/api/v1/instructor/assignments/' }
            ]
        },
        {
            title: 'Certificate Generation',
            description: 'Automated certificate generation and download',
            icon: 'fa-certificate',
            color: '#06b6d4',
            endpoints: [
                { end_point: '/api/v1/enrollment/certificates/' }
            ]
        }
    ],
    contact: {
        name: 'Your Name',
        title: 'Django Developer',
        description: 'Passionate Django developer specializing in scalable REST APIs and full-stack applications',
        email: 'your.email@example.com',
        social_links: [
            { platform: 'GitHub', url: 'https://github.com/yourusername', icon: 'fab fa-github', username: 'github.com/yourusername' },
            { platform: 'LinkedIn', url: 'https://linkedin.com/in/yourusername', icon: 'fab fa-linkedin', username: 'linkedin.com/in/yourusername' },
            { platform: 'Twitter', url: 'https://twitter.com/yourusername', icon: 'fab fa-twitter', username: '@yourusername' }
        ]
    },
    api_endpoints: {
        count: 100
    }
};

// State management
let featureData = [...dummyData.features];
let contactData = { ...dummyData.contact };
let highlightData = [...dummyData.highlights];
let apiEndpointsCount = dummyData.api_endpoints.count;
let currentTab = 'general';

// Transform features data from API format to internal format
function transformFeaturesData(data) {
    const featureMap = {};

    data.forEach(featureGroup => {
        const items = featureGroup.items.map(item => ({
            title: item.title,
            description: item.description,
            icon: item.icon,
            image: item.image || null,
            color: item.color || 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)'
        }));

        featureMap[featureGroup.title] = items;
    });

    return featureMap;
}

// Transform highlights data from API format
function transformHighlightsData(data) {
    return data.map(highlight => ({
        title: highlight.title,
        description: highlight.description,
        icon: highlight.icon,
        color: highlight.color,
        endpoints: highlight.endpoints.map(ep => ep.end_point)
    }));
}

// Transform contact data from API format
function transformContactData(data) {
    return {
        name: data.name,
        title: data.title,
        description: data.description,
        email: data.email,
        socialLinks: (data.social_links || []).map(link => ({
            platform: link.platform,
            url: link.url,
            icon: link.icon,
            username: link.username
        }))
    };
}

// Fetch data from APIs
async function fetchData() {
    try {
        const origin = window.location.origin;
        const url = origin + "/api/v1/site-info/";

        const response = await fetch(url, {
            method: "GET",
        });

        if (response.ok) {
            const data = await response.json();

            console.log('Backend data:', data);

            // Transform API data to internal format
            if (data.features && Array.isArray(data.features)) {
                featureData = transformFeaturesData(data.features);
            }

            if (data.highlights && Array.isArray(data.highlights)) {
                highlightData = transformHighlightsData(data.highlights);
            }

            if (data.contact) {
                contactData = transformContactData(data.contact);
            }

            // Get API endpoints count
            if (data.api_endpoints && data.api_endpoints.count !== undefined) {
                apiEndpointsCount = data.api_endpoints.count;
                console.log('API endpoints count:', apiEndpointsCount);
            }

            console.log('Using backend data');
        } else {
            console.warn('Failed to fetch site info, using dummy data');
            // Use dummy data
            featureData = [...dummyData.features];
            contactData = { ...dummyData.contact };
            highlightData = [...dummyData.highlights];
            apiEndpointsCount = dummyData.api_endpoints.count;
        }

    } catch (error) {
        console.error('Error fetching data:', error);
        console.warn('Using dummy data as fallback');
        // Fallback to dummy data
        featureData = [...dummyData.features];
        contactData = { ...dummyData.contact };
        highlightData = [...dummyData.highlights];
        apiEndpointsCount = dummyData.api_endpoints.count;
    } finally {
        // Render with available data
        renderHeroStats();
        renderFeatureTabs();
        renderHighlights();
        renderContactInfo();
        renderFooter();
    }
}

// Render hero stats with API endpoints count
function renderHeroStats() {
    const heroStats = document.querySelector('.hero-stats');

    if (heroStats) {
        heroStats.innerHTML = `
            <div class="stat-item">
                <h3>${apiEndpointsCount}</h3>
                <p>API Endpoints</p>
            </div>
        `;
    }
}

// Render feature tabs
function renderFeatureTabs() {
    const tabContainer = document.getElementById('tabContainer');
    const tabContents = document.getElementById('tabContents');

    if (!tabContainer || !tabContents) return;

    tabContainer.innerHTML = '';
    tabContents.innerHTML = '';

    // Check if featureData is array (API format) or object (old format)
    let tabs = [];

    if (Array.isArray(featureData)) {
        // API format - array of groups
        tabs = featureData.map(group => ({
            id: group.title || 'general',
            label: group.title ? group.title.charAt(0).toUpperCase() + group.title.slice(1) : 'General',
            icon: getTabIcon(group.title),
            items: group.items || []
        }));
    } else if (typeof featureData === 'object') {
        // Object format - keys are tab names
        const tabNames = Object.keys(featureData);
        tabs = tabNames.map(name => ({
            id: name,
            label: name.charAt(0).toUpperCase() + name.slice(1),
            icon: getTabIcon(name),
            items: featureData[name] || []
        }));
    }

    // Ensure we have at least default tabs
    if (tabs.length === 0) {
        tabs = [
            { id: 'general', label: 'General', icon: 'fa-globe', items: [] },
            { id: 'student', label: 'Student', icon: 'fa-user-graduate', items: [] },
            { id: 'instructor', label: 'Instructor', icon: 'fa-chalkboard-teacher', items: [] }
        ];
    }

    tabs.forEach((tab, index) => {
        const button = document.createElement('button');
        button.className = `tab-button ${index === 0 ? 'active' : ''}`;
        button.setAttribute('data-tab', tab.id);
        button.innerHTML = `<i class="fas ${tab.icon}"></i> ${tab.label}`;
        button.addEventListener('click', () => switchTab(tab.id));
        tabContainer.appendChild(button);
    });

    tabs.forEach((tab, index) => {
        const content = document.createElement('div');
        content.className = `tab-content ${index === 0 ? 'active' : ''}`;
        content.id = tab.id;

        const scrollContainer = document.createElement('div');
        scrollContainer.className = 'scroll-container';

        const leftArrow = document.createElement('button');
        leftArrow.className = 'scroll-arrow scroll-arrow-left';
        leftArrow.innerHTML = '<i class="fas fa-chevron-left"></i>';
        leftArrow.onclick = () => scrollCards(tab.id, -1);

        const grid = document.createElement('div');
        grid.className = 'role-grid';
        grid.id = `${tab.id}-grid`;

        const cards = tab.items || [];
        cards.forEach((card, cardIndex) => {
            grid.appendChild(createFeatureCard(card, tab.id, cardIndex));
        });

        const rightArrow = document.createElement('button');
        rightArrow.className = 'scroll-arrow scroll-arrow-right';
        rightArrow.innerHTML = '<i class="fas fa-chevron-right"></i>';
        rightArrow.onclick = () => scrollCards(tab.id, 1);

        scrollContainer.appendChild(leftArrow);
        scrollContainer.appendChild(grid);
        scrollContainer.appendChild(rightArrow);
        content.appendChild(scrollContainer);

        tabContents.appendChild(content);
    });

    // Set initial tab
    if (tabs.length > 0) {
        currentTab = tabs[0].id;
    }
}

// Helper function to get tab icon based on tab name
function getTabIcon(tabName) {
    const icons = {
        'general': 'fa-globe',
        'student': 'fa-user-graduate',
        'instructor': 'fa-chalkboard-teacher'
    };
    return icons[tabName] || 'fa-globe';
}

// Create feature card
function createFeatureCard(card, tabId, index) {
    const cardElement = document.createElement('div');
    cardElement.className = 'role-card';
    cardElement.onclick = () => openModal(tabId, index, card);

    const imageContainer = document.createElement('div');
    imageContainer.className = 'role-card-image';

    if (card.image && card.image !== null && card.image !== '') {
        // Use image if available
        const img = document.createElement('img');
        img.src = card.image;
        img.alt = card.title || 'Feature image';
        img.onerror = function() {
            // Fallback to icon if image fails to load
            this.remove();
            imageContainer.style.background = card.color || 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)';
            const icon = document.createElement('i');
            icon.className = `fas ${card.icon || 'fa-star'}`;
            imageContainer.appendChild(icon);
        };
        imageContainer.appendChild(img);
    } else {
        // Use icon if no image
        imageContainer.style.background = card.color || 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)';
        const icon = document.createElement('i');
        icon.className = `fas ${card.icon || 'fa-star'}`;
        imageContainer.appendChild(icon);
    }

    const content = document.createElement('div');
    content.className = 'role-card-content';

    const title = document.createElement('h3');
    title.textContent = card.title || 'Untitled';

    const description = document.createElement('p');
    description.textContent = card.description || 'No description available';

    content.appendChild(title);
    content.appendChild(description);

    cardElement.appendChild(imageContainer);
    cardElement.appendChild(content);

    return cardElement;
}

// Switch tab
function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabId);
    });
}

// Scroll cards
function scrollCards(tabId, direction) {
    const grid = document.getElementById(`${tabId}-grid`);
    if (grid) {
        grid.scrollBy({ left: 300 * direction, behavior: 'smooth' });
    }
}

// Render highlights
function renderHighlights() {
    const highlightsGrid = document.getElementById('highlightsGrid');
    if (!highlightsGrid) return;

    highlightsGrid.innerHTML = '';

    highlightData.forEach(highlight => {
        const card = document.createElement('div');
        card.className = 'highlight-card';

        const icon = document.createElement('div');
        icon.className = 'highlight-icon';
        icon.style.background = `${highlight.color}20`;
        icon.style.color = highlight.color;
        icon.innerHTML = `<i class="fas ${highlight.icon}"></i>`;

        const title = document.createElement('h3');
        title.textContent = highlight.title;

        const description = document.createElement('p');
        description.textContent = highlight.description;

        const endpointsDiv = document.createElement('div');
        endpointsDiv.className = 'highlight-endpoints';

        const endpoints = highlight.endpoints || [];
        endpoints.forEach(endpoint => {
            const tag = document.createElement('span');
            tag.className = 'endpoint-tag';
            tag.textContent = endpoint;
            endpointsDiv.appendChild(tag);
        });

        card.appendChild(icon);
        card.appendChild(title);
        card.appendChild(description);
        card.appendChild(endpointsDiv);

        highlightsGrid.appendChild(card);
    });
}

// Render contact info
function renderContactInfo() {
    const contactInfo = document.getElementById('contactInfo');
    if (!contactInfo) return;

    contactInfo.innerHTML = '';

    const heading = document.createElement('h3');
    heading.textContent = "Let's Connect!";

    const description = document.createElement('p');
    description.textContent = contactData.description || 'Feel free to reach out!';

    const socialLinks = document.createElement('div');
    socialLinks.className = 'social-links';

    const emailLink = document.createElement('a');
    emailLink.href = `mailto:${contactData.email}`;
    emailLink.className = 'social-link';
    emailLink.innerHTML = `
        <i class="fas fa-envelope"></i>
        <div>
            <strong>Email</strong>
            <p style="margin: 0; font-size: 0.9rem;">${contactData.email}</p>
        </div>
    `;
    socialLinks.appendChild(emailLink);

    const socialLinksData = contactData.socialLinks || [];
    socialLinksData.forEach(link => {
        const socialLink = document.createElement('a');
        socialLink.href = link.url;
        socialLink.target = '_blank';
        socialLink.className = 'social-link';
        socialLink.innerHTML = `
            <i class="${link.icon}"></i>
            <div>
                <strong>${link.platform}</strong>
                <p style="margin: 0; font-size: 0.9rem;">${link.username}</p>
            </div>
        `;
        socialLinks.appendChild(socialLink);
    });

    contactInfo.appendChild(heading);
    contactInfo.appendChild(description);
    contactInfo.appendChild(socialLinks);
}

// Render footer
function renderFooter() {
    const footerLinks = document.getElementById('footerLinks');
    if (!footerLinks) return;

    footerLinks.innerHTML = '';

    const links = [
        { text: 'Sign Up', url: '/account/auth/signup/', icon: 'fa-user-plus' },
        { text: 'Login', url: '/account/auth/login/', icon: 'fa-sign-in-alt' },
        { text: 'Contact', url: '#contact', icon: 'fa-envelope' }
    ];

    const socialLinksData = contactData.socialLinks || [];
    socialLinksData.forEach(link => {
        links.push({ text: link.platform, url: link.url, icon: link.icon });
    });

    links.forEach(link => {
        const a = document.createElement('a');
        a.href = link.url;
        if (link.url.startsWith('http')) a.target = '_blank';
        a.innerHTML = `<i class="fas ${link.icon}"></i> ${link.text}`;
        footerLinks.appendChild(a);
    });
}

// Modal functions
function openModal(tabId, cardIndex, card) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modalTitle');
    const modalDescription = document.getElementById('modalDescription');

    if (!modal || !modalImage || !modalTitle || !modalDescription) return;

    modalImage.innerHTML = '';

    if (card.image && card.image !== null && card.image !== '') {
        const img = document.createElement('img');
        img.src = card.image;
        img.alt = card.title || 'Feature image';
        img.onerror = function() {
            // Fallback to icon if image fails to load
            this.remove();
            modalImage.style.background = card.color || 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)';
            modalImage.innerHTML = `<i class="fas ${card.icon || 'fa-star'}"></i>`;
        };
        modalImage.appendChild(img);
    } else {
        modalImage.style.background = card.color || 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)';
        modalImage.innerHTML = `<i class="fas ${card.icon || 'fa-star'}"></i>`;
    }

    modalTitle.textContent = card.title || 'Untitled';
    modalDescription.textContent = card.description || 'No description available';

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

// Contact form submission
async function submitContactForm(formData) {
    const formFeedback = document.getElementById('formFeedback');
    const submitBtn = document.getElementById('submitBtn');
    const contactForm = document.getElementById('contactForm');

    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    }

    // Hide previous feedback
    if (formFeedback) {
        formFeedback.style.display = 'none';
        formFeedback.className = 'form-feedback';
    }

    try {
        const origin = window.location.origin;
        const url = origin + "/api/v1/message/";

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            if (formFeedback) {
                formFeedback.textContent = '✅ Message sent successfully! I\'ll get back to you soon.';
                formFeedback.style.color = 'var(--color-success)';
                formFeedback.className = 'form-feedback show success';
                formFeedback.style.display = 'block';
            }

            if (contactForm) {
                contactForm.reset();
            }
        } else {
            if (formFeedback) {
                formFeedback.textContent = `${data.detail || 'Something went wrong. Please try again.'}`;
                formFeedback.style.color = 'var(--color-error)';
                formFeedback.className = 'form-feedback show error';
                formFeedback.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error submitting form:', error);
        if (formFeedback) {
            formFeedback.textContent = '❌ Failed to send. Please try again later.';
            formFeedback.style.color = 'var(--color-error)';
            formFeedback.className = 'form-feedback show error';
            formFeedback.style.display = 'block';
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Message';
        }
    }

    console.log('Contact form submitted:', formData);
    return true;
}

// CSRF token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Hamburger menu functionality
function initHamburgerMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const navbarMenu = document.getElementById('navbarMenu');

    if (hamburgerBtn && navbarMenu) {
        hamburgerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Hamburger clicked');

            hamburgerBtn.classList.toggle('active');
            navbarMenu.classList.toggle('active');

            console.log('Menu active:', navbarMenu.classList.contains('active'));
        });

        // Close menu when a link is clicked
        const menuLinks = navbarMenu.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                hamburgerBtn.classList.remove('active');
                navbarMenu.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarMenu.contains(e.target) && !hamburgerBtn.contains(e.target)) {
                hamburgerBtn.classList.remove('active');
                navbarMenu.classList.remove('active');
            }
        });

        // Close menu on window resize (if going to desktop)
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                hamburgerBtn.classList.remove('active');
                navbarMenu.classList.remove('active');
            }
        });
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    initHamburgerMenu();

    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
    });

    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                subject: document.getElementById('subject').value,
                message: document.getElementById('message').value
            };

            await submitContactForm(formData);
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    const year = new Date().getFullYear();
    const footerText = document.getElementById('footerText');
    if (footerText) {
        footerText.textContent += ` © ${year}`;
    }
});
