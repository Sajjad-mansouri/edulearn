// ==================== UTILITY FUNCTIONS ====================

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';

    try {
        const date = new Date(dateTimeString);

        if (isNaN(date.getTime())) return dateTimeString;

        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        const diffWeeks = Math.floor(diffDays / 7);
        const diffMonths = Math.floor(diffDays / 30);
        const diffYears = Math.floor(diffDays / 365);

        if (diffSecs < 60) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        if (diffWeeks < 5) return `${diffWeeks} week${diffWeeks > 1 ? 's' : ''} ago`;
        if (diffMonths < 12) return `${diffMonths} month${diffMonths > 1 ? 's' : ''} ago`;
        return `${diffYears} year${diffYears > 1 ? 's' : ''} ago`;
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateTimeString;
    }
}

function formatLastUpdated(dateTimeString) {
    if (!dateTimeString) return '';

    try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) return dateTimeString;

        const months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        const month = months[date.getMonth()];
        const year = date.getFullYear();

        return `${month} ${year}`;
    } catch (error) {
        console.error('Error formatting last updated:', error);
        return dateTimeString;
    }
}

// ==================== API SERVICE ====================
class CourseApiService {
    static async fetchCourseDetail(courseId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/`,
            {
                method: "GET",
            }
        );

        if (!response.ok) throw new Error('Failed to fetch course detail ');
        const data = await response.json();

        return data;
    }

    static async fetchInstructor(courseId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/instructor/`,
            {
                method: "GET",
            }
        );

        if (!response.ok) throw new Error('Failed to fetch course detail ');
        const data = await response.json();

        return data;
    }

    static async fetchCurriculum(courseId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/curriculum/`,
            {
                method: "GET",
            }
        );

        if (!response.ok) throw new Error('Failed to fetch course curriculum ');
        const data = await response.json();
        return new Promise(resolve => resolve(data.results));
    }

    static async fetchReviews(courseId, page = 1, perPage = 3) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/reviews/?page_number=${page}&per_page=${perPage}`,
            {
                method: "GET",
            }
        );

        if (!response.ok) throw new Error('Failed to fetch course curriculum ');
        const data = await response.json();

        return new Promise(resolve => resolve(data));

    }

    static async submitReview(courseId, rating, comment) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/submit/review/`,
            {
                method: "POST",
                body: JSON.stringify({ rating, comment })
            }
        );

        if (!response.ok) throw new Error('Failed to fetch course curriculum ');
        const data = await response.json();

        return new Promise(resolve => resolve({ success: true, message: 'Review submitted successfully' }));
    }

    static async toggleReviewHelpful(courseId, reviewId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/reviews/${reviewId}/helpful/`,
            {
                method: "POST",
            }
        );

        if (!response.ok) throw new Error('Failed to toggle review helpful');
        const data = await response.json();

        return new Promise(resolve =>  resolve({
            success: true,
            helpful_count: data.helpful_count,
            user_has_liked: data.user_has_liked
        }));
    }

    static async deleteReview(courseId, reviewId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/reviews/${reviewId}/delete/`,
            {
                method: "DELETE",
            }
        );

        if (!response.ok) throw new Error('Failed to delete review');


    }

    static async checkAuth() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/auth/current-user/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) throw new Error('Failed to fetch current user');
            const data = await response.json()

            return data

        } catch (error) {
            console.error('Error loading current user:', error);
        }

        return new Promise(resolve => resolve({"is_authenticated":false}));
    }

    static async toggleWishlist(courseId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/courses/${courseId}/wishlist/`,
            {
                method: "POST",
            }
        );

        if (!response.ok) throw new Error('Failed to toggle wishlist');
        const data = await response.json()

        return data
    }

    static async checkWishlistStatus(courseId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/courses/${courseId}/wishlist/status/`,
                {
                    method: "GET",
                }
            );

            if (!response.ok) throw new Error('Failed to fetch wishlist status');
            const data = await response.json();

            return data;
        } catch (error) {
            console.error('Error checking wishlist status:', error);
            return { is_wishlisted: false };
        }
    }

    static async checkEnrollment(courseId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/enrollment/user-enrollment-status/${courseId}/`,
                {
                    method: "GET",
                }
            );

            if (!response.ok) throw new Error('Failed to fetch enrollment status');
            const data = await response.json()

            return data

        } catch (error) {
            console.error('Error loading enrollment status:', error);
        }

        return new Promise(resolve => resolve({ is_enrolled: false }));
    }

    static async enrollInCourse(courseId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/enrollment/enroll/${courseId}/`,
            {
                method: "POST",
            }
        );

        if (!response.ok) throw new Error('Failed to enroll in course');
        const data = await response.json();

        return data;
    }

    static async createEnrollmentCheckout(enrollmentId) {
        const response = await auth.authenticatedRequest(
            baseUrl + `/api/v1/payment/enrollments/${enrollmentId}/checkout/`,
            {
                method: "POST",
            }
        );

        if (!response.ok) throw new Error('Failed to create checkout session');
        const data = await response.json();

        return data;
    }
}

// ==================== SKELETON LOADING SYSTEM ====================
class SkeletonLoader {
    static injectStyles() {
        if (document.getElementById('skeleton-loader-styles')) return;

        const style = document.createElement('style');
        style.id = 'skeleton-loader-styles';
        style.textContent = `
            @keyframes shimmer {
                0% { background-position: -468px 0; }
                100% { background-position: 468px 0; }
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.4; }
            }

            .skeleton-box {
                background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
                background-size: 936px 100%;
                animation: shimmer 1.5s infinite linear;
                border-radius: 4px;
                display: block;
            }

            .skeleton-text {
                background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
                background-size: 936px 100%;
                animation: shimmer 1.5s infinite linear;
                border-radius: 4px;
                height: 16px;
                margin-bottom: 8px;
            }

            .skeleton-text-lg {
                height: 24px;
                margin-bottom: 12px;
            }

            .skeleton-text-xl {
                height: 32px;
                margin-bottom: 16px;
            }

            .skeleton-circle {
                border-radius: 50%;
                background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
                background-size: 936px 100%;
                animation: shimmer 1.5s infinite linear;
            }

            .skeleton-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 16px;
                border: 1px solid #e5e7eb;
            }

            .skeleton-hidden {
                visibility: hidden;
                position: absolute;
                pointer-events: none;
            }

            .skeleton-overlay {
                position: relative;
            }

            .hero-placeholder {
                min-height: 400px;
            }

            .enrollment-card-skeleton {
                width: 380px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.08);
                overflow: hidden;
            }
        `;
        document.head.appendChild(style);
    }

    static hideOriginalContent() {
        const heroContent = document.querySelector('.course-hero-content');
        const enrollmentCard = document.querySelector('.enrollment-card');
        const tabContents = document.querySelectorAll('.tab-content');

        if (heroContent) {
            heroContent.style.visibility = 'hidden';
            heroContent.style.position = 'absolute';
        }

        if (enrollmentCard) {
            enrollmentCard.style.visibility = 'hidden';
            enrollmentCard.style.position = 'absolute';
        }

        tabContents.forEach(tab => {
            tab.style.visibility = 'hidden';
            tab.style.position = 'absolute';
        });
    }

    static showHeroSkeleton() {
        const heroInner = document.querySelector('.course-hero-inner');
        if (!heroInner) return;

        this.hideOriginalContent();

        const leftSkeleton = document.createElement('div');
        leftSkeleton.className = 'course-hero-content skeleton-placeholder';
        leftSkeleton.style.cssText = 'flex: 1; padding-right: 40px;';
        leftSkeleton.innerHTML = `
            <div class="skeleton-text" style="width: 200px; margin-bottom: 20px;"></div>
            <div class="skeleton-text skeleton-text-xl" style="width: 80%;"></div>
            <div class="skeleton-text skeleton-text-lg" style="width: 60%;"></div>
            <div class="skeleton-text" style="width: 70%; margin-top: 30px;"></div>
            <div style="display: flex; align-items: center; gap: 16px; margin-top: 30px;">
                <div class="skeleton-circle" style="width: 48px; height: 48px;"></div>
                <div>
                    <div class="skeleton-text" style="width: 180px;"></div>
                    <div class="skeleton-text" style="width: 140px;"></div>
                </div>
            </div>
            <div class="skeleton-text" style="width: 250px; margin-top: 20px;"></div>
        `;

        const rightSkeleton = document.createElement('div');
        rightSkeleton.className = 'enrollment-card-skeleton skeleton-placeholder';
        rightSkeleton.style.cssText = 'flex-shrink: 0;';
        rightSkeleton.innerHTML = `
            <div class="skeleton-box" style="width: 100%; height: 200px; border-radius: 0;"></div>
            <div style="padding: 24px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    <div class="skeleton-text skeleton-text-xl" style="width: 80px;"></div>
                    <div class="skeleton-text" style="width: 60px;"></div>
                    <div class="skeleton-text" style="width: 80px;"></div>
                </div>
                <div class="skeleton-box" style="width: 100%; height: 48px; margin-bottom: 12px;"></div>
                <div class="skeleton-box" style="width: 100%; height: 48px; margin-bottom: 20px;"></div>
                <div class="skeleton-text" style="width: 200px; margin-bottom: 20px;"></div>
                ${Array(5).fill('').map(() => '<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div class="skeleton-circle" style="width: 20px; height: 20px;"></div><div class="skeleton-text" style="width: 70%;"></div></div>').join('')}
                <div style="display: flex; gap: 12px; margin-top: 20px;">
                    <div class="skeleton-circle" style="width: 36px; height: 36px;"></div>
                    <div class="skeleton-circle" style="width: 36px; height: 36px;"></div>
                    <div class="skeleton-circle" style="width: 36px; height: 36px;"></div>
                    <div class="skeleton-circle" style="width: 36px; height: 36px;"></div>
                </div>
            </div>
        `;

        heroInner.appendChild(leftSkeleton);
        heroInner.appendChild(rightSkeleton);
    }

    static showTabsSkeleton() {
        const tabsContainer = document.getElementById('detailTabs');
        const detailMain = document.querySelector('.course-detail-main');
        if (!detailMain) return;

        const tabSkeleton = document.createElement('div');
        tabSkeleton.className = 'skeleton-placeholder tab-skeleton';
        tabSkeleton.style.cssText = 'margin-top: 24px;';
        tabSkeleton.innerHTML = `
            <div class="skeleton-card">
                <div class="skeleton-text skeleton-text-lg" style="width: 300px; margin-bottom: 24px;"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    ${Array(8).fill('').map(() => '<div class="skeleton-text" style="width: 90%; margin-bottom: 12px;"></div>').join('')}
                </div>
            </div>
            <div class="skeleton-card">
                <div class="skeleton-text skeleton-text-lg" style="width: 250px; margin-bottom: 24px;"></div>
                <div class="skeleton-text" style="width: 100%; margin-bottom: 8px;"></div>
                <div class="skeleton-text" style="width: 95%; margin-bottom: 8px;"></div>
                <div class="skeleton-text" style="width: 88%; margin-bottom: 8px;"></div>
                <div class="skeleton-text" style="width: 92%; margin-bottom: 8px;"></div>
                <div class="skeleton-text" style="width: 40%;"></div>
            </div>
        `;

        if (tabsContainer) {
            tabsContainer.after(tabSkeleton);
        } else {
            detailMain.appendChild(tabSkeleton);
        }
    }

    static removeSkeletons() {
        document.querySelectorAll('.skeleton-placeholder').forEach(el => el.remove());

        const heroContent = document.querySelector('.course-hero-content');
        const enrollmentCard = document.querySelector('.enrollment-card');
        const tabContents = document.querySelectorAll('.tab-content');

        if (heroContent) {
            heroContent.style.visibility = '';
            heroContent.style.position = '';
        }

        if (enrollmentCard) {
            enrollmentCard.style.visibility = '';
            enrollmentCard.style.position = '';
        }

        tabContents.forEach(tab => {
            tab.style.visibility = '';
            tab.style.position = '';
        });
    }
}

// ==================== COURSE DETAIL PAGE CLASS ====================
class CourseDetailPage {
    constructor() {
        this.courseSlug = this.getSlugFromUrl();
        this.courseId = this.getCourseId();

        this.courseData = null;
        this.instructorData = null;
        this.curriculumData = null;
        this.reviewsData = null;
        this.userAuth = null;
        this.activeTab = 'overview';
        this.currentReviewPage = 1;
        this.isLoadingMoreReviews = false;
        this.currentRating = null;
        this.isEnrolled = false;
        this.isWishlisted = false;
        this.currentVideoPlayer = null;
        this.processingHelpfulReviews = new Set();
        this.processingDeleteReviews = new Set();
        this.activeDropdown = null;
        this.isEnrolling = false;
        this.init();
    }

    getSlugFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/courses\/(\d+)\/([^/]+)/);
        return match ? match[2] : 'python-for-data-science';
    }

    getCourseId(){
        const container = document.getElementById('courseDetailContainer');
        if (container?.dataset.courseId) {
            return parseInt(container.dataset.courseId);
        }

        const path = window.location.pathname;
        const match = path.match(/\/courses\/(\d+)\//)
        if (match){
            return parseInt(match[1])
        }

        return null;
    }

    async init() {
        this.bindEvents();
        this.bindGlobalClickHandler();

        SkeletonLoader.injectStyles();
        SkeletonLoader.showHeroSkeleton();
        SkeletonLoader.showTabsSkeleton();

        await this.checkAuth();
        await this.loadAllData();
        this.bindHelpfulButtons();
        this.bindDropdownButtons();

        SkeletonLoader.removeSkeletons();
    }

    escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    }

    bindGlobalClickHandler() {
        document.addEventListener('click', (e) => {
            if (this.activeDropdown && !e.target.closest('.review-dropdown-menu') && !e.target.closest('.review-three-dot-btn')) {
                this.closeAllDropdowns();
            }
        });
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.review-dropdown-menu');
        dropdowns.forEach(dropdown => {
            dropdown.style.display = 'none';
        });
        this.activeDropdown = null;
    }

    async checkAuth() {
        try {
            this.userAuth = await CourseApiService.checkAuth();


            if (this.userAuth.is_authenticated) {
                const [enrollmentData, wishlistData] = await Promise.all([
                    CourseApiService.checkEnrollment(this.courseId),
                    CourseApiService.checkWishlistStatus(this.courseId)
                ]);

                this.isEnrolled = enrollmentData.is_enrolled;
                this.isWishlisted = wishlistData.is_wishlisted;
                this.enrollment_id = enrollmentData.enrollment_id
                this.updateWishlistButton();
            }

        } catch (error) {
            console.error('Failed to check auth:', error);
            this.userAuth = { is_authenticated: false };
            this.isEnrolled = false;
            this.isWishlisted = false;
        }
    }

    updateWishlistButton() {
        const btn = document.getElementById('wishlistBtn');
        if (!btn) return;

        if (this.isWishlisted) {
            btn.innerHTML = '<i class="fas fa-heart"></i> Saved to Wishlist';
            btn.classList.add('wishlisted');
        } else {
            btn.innerHTML = '<i class="far fa-heart"></i> Add to Wishlist';
            btn.classList.remove('wishlisted');
        }
    }

    async loadAllData() {
        try {
            const [courseData, instructorData, curriculumData, reviewsData] = await Promise.all([
                CourseApiService.fetchCourseDetail(this.courseId),
                CourseApiService.fetchInstructor(this.courseId),
                CourseApiService.fetchCurriculum(this.courseId),
                CourseApiService.fetchReviews(this.courseId, 1, 3)
            ]);

            this.courseData = courseData;

            this.instructorData = instructorData;
            this.curriculumData = curriculumData;
            this.reviewsData = reviewsData;

            this.populateHeroSection();
            this.populateOverviewTab();
            this.populateCurriculumTab();
            this.populateInstructorTab();
            this.populateReviewsTab();
            this.updateTabCounts();

        } catch (error) {
            console.error('Failed to load course data:', error);
            this.showToast('Failed to load course data. Please try again.', 'error');
        }
    }

    populateHeroSection() {
        const data = this.courseData;

        const titleEl = document.querySelector('.course-hero-title');
        const subtitleEl = document.querySelector('.course-hero-subtitle');
        if (titleEl) titleEl.textContent = data.title;
        if (subtitleEl) subtitleEl.textContent = data.subtitle;

        const lastUpdatedEl = document.querySelector('.course-hero-dates span');
        if (lastUpdatedEl && data.last_updated) {
            lastUpdatedEl.textContent = `Last updated: ${formatLastUpdated(data.last_updated)}`;
        }

        const metaContainer = document.querySelector('.course-hero-meta');
        if (metaContainer) {
            metaContainer.innerHTML = `
                <span class="meta-badge"><i class="fas fa-star"></i> ${this.escapeHtml(String(data.rating))} (${this.escapeHtml(String(data.total_ratings))} ratings)</span>
                <span class="meta-badge"><i class="fas fa-users"></i> ${this.escapeHtml(String(data.total_students))} students</span>
                <span class="meta-badge"><i class="fas fa-clock"></i> ${this.escapeHtml(String(data.duration))} hours</span>
                <span class="meta-badge"><i class="fas fa-signal"></i> ${this.escapeHtml(data.level)}</span>
                <span class="meta-badge"><i class="fas fa-globe"></i> ${this.escapeHtml(data.language)}</span>
                <span class="meta-badge"><i class="fas fa-closed-captioning"></i> ${this.escapeHtml(data.subtitles.join(', '))}</span>
            `;
        }

        if (this.instructorData) {
            const instructorEl = document.querySelector('.course-hero-instructor');
            if (instructorEl) {
                const instructor = this.instructorData;
                instructorEl.innerHTML = `
                    <img src="${this.escapeHtml(instructor.avatar.replace('size=220', 'size=80'))}" alt="${this.escapeHtml(instructor.name)}" class="instructor-avatar-sm">
                    <span>Created by <strong>${this.escapeHtml(instructor.name)}</strong></span>
                    ${instructor.is_verified ? '<span class="verified-badge-sm"><i class="fas fa-check-circle"></i> Verified Instructor</span>' : ''}
                    ${instructor.organization ? `<span class="org-badge-sm"><i class="fas fa-building-columns"></i> ${this.escapeHtml(instructor.organization)}</span>` : ''}
                `;
            }
        }

        this.updateEnrollmentCard();
    }

    updateEnrollmentCard() {
        const data = this.courseData;

        const thumbImg = document.querySelector('.enrollment-card-thumb img');
        if (thumbImg) thumbImg.src = data.thumbnail;

        if (this.isEnrolled) {
            const priceSection = document.querySelector('.enrollment-price-section');
            if (priceSection) {
                priceSection.innerHTML = `
                    <div style="text-align: center; padding: 0.5rem 0;">
                        <span style="background: #10B981; color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9rem;">
                            <i class="fas fa-check-circle"></i> Enrolled
                        </span>
                    </div>
                `;
            }
        } else {
            const priceEl = document.querySelector('.current-price');
            const originalPriceEl = document.querySelector('.original-price');
            const discountBadge = document.querySelector('.discount-badge');

            if (data.original_price === "free") {
                if (priceEl) {
                    priceEl.textContent = "Free";
                }

                if (originalPriceEl) {
                    originalPriceEl.textContent = "";
                }

                if (discountBadge) {
                    discountBadge.remove();
                }
            } else {
                if (priceEl) {
                    priceEl.textContent = `$${data.price}`;
                }

                if (originalPriceEl) {
                    originalPriceEl.textContent = `$${data.original_price}`;
                }

                if (discountBadge) {
                    discountBadge.textContent = `${data.price_discount}% OFF`;
                }
            }
        }

        const enrollBtn = document.getElementById('enrollBtn');
        const wishlistBtn = document.getElementById('wishlistBtn');
        const moneyBack = document.querySelector('.money-back');

        if (enrollBtn) {
            if (this.isEnrolled) {
                enrollBtn.outerHTML = `
                    <button class="enroll-btn-primary" id="goToCourseBtn" style="background: #10B981;">
                        <i class="fas fa-play-circle"></i> Go to Course
                    </button>
                `;
                document.getElementById('goToCourseBtn')?.addEventListener('click', () => {
                    window.location.href = `/enrollment/${this.enrollment_id}/learn/`;
                });
            } else {
                // Check if user is an instructor
                if (this.userAuth && this.userAuth.is_instructor) {
                    enrollBtn.style.display = 'none';
                } else {
                    enrollBtn.innerHTML = '<i class="fas fa-rocket"></i> Enroll Now';
                    enrollBtn.onclick = () => this.handleEnrollClick();
                }
            }
        }

        if (wishlistBtn) {
            if (this.userAuth && this.userAuth.is_instructor) {
                wishlistBtn.style.display = 'none';
            } else {
                wishlistBtn.style.display = this.isEnrolled ? 'none' : '';
                if (!this.isEnrolled) {
                    this.updateWishlistButton();
                }
            }
        }

        if (moneyBack) {
            moneyBack.style.display = (this.isEnrolled || (this.userAuth && this.userAuth.is_instructor)) ? 'none' : '';
        }

        const featuresContainer = document.querySelector('.enrollment-features');
        if (featuresContainer && data.features) {
            featuresContainer.innerHTML = data.features.map(f => `
                <div class="feature-item">
                    <i class="fas ${this.escapeHtml(f.icon)}"></i>
                    <span>${this.escapeHtml(f.text)}</span>
                </div>
            `).join('');
        }
    }

    populateOverviewTab() {
        const data = this.courseData;

        const outcomesContainer = document.getElementById('learningOutcomes');
        if (outcomesContainer && data.learning_outcomes) {
            outcomesContainer.innerHTML = data.learning_outcomes.map(outcome => `
                <div class="outcome-item-pub"><i class="fas fa-check"></i> ${this.escapeHtml(outcome)}</div>
            `).join('');
        }

        const descContainer = document.getElementById('courseDescription');
        if (descContainer && data.description) {
            let description = data.description;

            // Remove "(updated)" prefix if present
            if (description.startsWith('(updated)')) {
                description = description.replace('(updated)', '').trim();
            }

            // Replace literal \n with actual newlines
            description = description.replace(/\\n/g, '\n');

            // Use textContent to safely set the text
            descContainer.textContent = description;
        }

        const prereqContainer = document.getElementById('prerequisitesList');
        if (prereqContainer && data.prerequisites) {
            prereqContainer.innerHTML = data.prerequisites.map(prereq => `
                <li><i class="fas fa-check-circle"></i> ${this.escapeHtml(prereq)}</li>
            `).join('');
        }

        const audienceContainer = document.getElementById('audienceTags');
        if (audienceContainer && data.target_audience) {
            audienceContainer.innerHTML = data.target_audience.map(audience => `
                <span class="audience-tag">${this.escapeHtml(audience)}</span>
            `).join('');
        }
    }

    populateCurriculumTab() {
        const container = document.getElementById('curriculumSections');
        if (!container || !this.curriculumData) return;

        const totalLessons = this.curriculumData.reduce((sum, section) => sum + (section.lessons_count || section.lessons?.length || 0), 0);
        const headerBar = document.querySelector('.curriculum-header-bar');
        if (headerBar) {

            headerBar.innerHTML = `
                <span><strong>${this.escapeHtml(String(this.curriculumData.length))} sections</strong> · <strong>${this.escapeHtml(String(totalLessons))} lessons</strong> · <strong>${this.escapeHtml(String(this.courseData.duration))} total length</strong></span>
                <button class="expand-all-btn" id="expandAllBtn">Expand All</button>
            `;
        }

        container.innerHTML = this.curriculumData.map((section, sectionIndex) => {
            const lessons = section.lessons || [];
            const isLocked = section.is_locked && !this.isEnrolled;

            const lessonsHtml = isLocked ? `
                <div class="curriculum-lessons" style="display:none;">
                    <div class="curriculum-lesson">
                        <div class="lesson-info">
                            <i class="fas fa-lock lesson-type-icon"></i>
                            <span class="lesson-title">Enroll to unlock full curriculum</span>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="curriculum-lessons" style="display:none;">
                    ${lessons.map((lesson, lessonIndex) => this.createLessonItem(lesson, sectionIndex, lessonIndex)).join('')}
                </div>
            `;

            return `
                <div class="curriculum-section" data-section-index="${this.escapeHtml(String(sectionIndex))}">
                    <div class="curriculum-section-header" onclick="toggleCurriculumSection(this)">
                        <div class="curriculum-section-info">
                            <i class="fas fa-chevron-down section-arrow"></i>
                            <h4>${this.escapeHtml(section.title)}</h4>
                            <span class="section-meta">${this.escapeHtml(String(section.lessons_count || lessons.length))} lessons · ${this.escapeHtml(section.total_duration)}</span>
                        </div>
                    </div>
                    ${lessonsHtml}
                </div>
            `;
        }).join('');

        this.attachPreviewHandlers();
        setTimeout(() => this.bindCurriculumEvents(), 0);
    }

    createLessonItem(lesson, sectionIndex, lessonIndex) {
        const typeIcons = {
            video: 'fa-play-circle',
            article: 'fa-file-lines article',
            quiz: 'fa-circle-question quiz',
            assignment: 'fa-tasks assignment'
        };


        const iconClass = typeIcons[lesson.type] || 'fa-file';
        const previewBadge = lesson.is_previewable ?
            '<span class="lesson-meta"><i class="fas fa-eye"></i> Preview</span>' : '';
        const previewClass = lesson.is_previewable ? 'previewable' : '';
        const dataAttrs = lesson.is_previewable ?
            `data-preview="true" data-section="${this.escapeHtml(String(sectionIndex))}" data-lesson="${this.escapeHtml(String(lessonIndex))}"` : '';

        return `
            <div class="curriculum-lesson ${previewClass}" ${dataAttrs}>
                <div class="lesson-info">
                    <i class="fas ${iconClass} lesson-type-icon"></i>
                    <span class="lesson-title">${this.escapeHtml(lesson.title)}</span>
                    ${previewBadge}
                </div>
                <span class="lesson-duration">${this.escapeHtml(lesson.duration)}</span>
            </div>
        `;
    }

    attachPreviewHandlers() {
        const previewLessons = document.querySelectorAll('.curriculum-lesson[data-preview="true"]');
        previewLessons.forEach(lessonEl => {
            lessonEl.style.cursor = 'pointer';
            lessonEl.addEventListener('click', (e) => {
                const sectionIndex = parseInt(lessonEl.dataset.section);
                const lessonIndex = parseInt(lessonEl.dataset.lesson);
                this.previewLesson(sectionIndex, lessonIndex);
            });
        });
    }

    bindCurriculumEvents() {
        const expandAllBtn = document.getElementById('expandAllBtn');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => this.toggleAllCurriculumSections());
        }
    }

    toggleAllCurriculumSections() {
        const sections = document.querySelectorAll('.curriculum-section-header');
        const allExpanded = Array.from(sections).every(s => s.classList.contains('open'));

        sections.forEach(section => {
            if (allExpanded) {
                section.classList.remove('open');
                const lessons = section.nextElementSibling;
                if (lessons) lessons.style.display = 'none';
            } else {
                section.classList.add('open');
                const lessons = section.nextElementSibling;
                if (lessons) lessons.style.display = '';
            }
        });

        const btn = document.getElementById('expandAllBtn');
        if (btn) btn.textContent = allExpanded ? 'Expand All' : 'Collapse All';
    }

    populateInstructorTab() {
        const container = document.getElementById('tabInstructor');
        if (!container || !this.instructorData) return;

        const instructor = this.instructorData;

        // Process bio text - replace literal \n with actual newlines
        let bioText = instructor.bio || '';
        bioText = bioText.replace(/\\n/g, '\n');

        container.innerHTML = `
            <div class="instructor-profile-card">
                <div class="instructor-profile-header">
                    <img src="${this.escapeHtml(instructor.avatar)}" alt="${this.escapeHtml(instructor.name)}" class="instructor-profile-avatar">
                    <div class="instructor-profile-info">
                        <h3>${this.escapeHtml(instructor.name)}</h3>
                        <p class="instructor-headline">${this.escapeHtml(instructor.headline)}</p>
                        <div class="instructor-badges">
                            ${instructor.is_verified ? '<span class="instructor-badge-pub"><i class="fas fa-check-circle"></i> Verified Instructor</span>' : ''}
                            <span class="instructor-badge-pub"><i class="fas fa-star"></i> ${this.escapeHtml(String(instructor.rating))} Instructor Rating</span>
                            <span class="instructor-badge-pub"><i class="fas fa-users"></i> ${this.escapeHtml(String(instructor.total_students))}+ Students</span>
                            <span class="instructor-badge-pub"><i class="fas fa-book"></i> ${this.escapeHtml(String(instructor.total_courses))} Courses</span>
                        </div>
                    </div>
                </div>
                <div class="instructor-profile-body" id="instructorBio" style="white-space: pre-line;">
                    ${this.escapeHtml(bioText)}
                </div>
                ${instructor.social_links ? `
                    <div style="padding: 1rem 0; display: flex; gap: 10px;">
                        ${instructor.social_links.twitter ? `<a href="${this.escapeHtml(instructor.social_links.twitter)}" target="_blank" class="share-icon-btn"><i class="fab fa-twitter"></i></a>` : ''}
                        ${instructor.social_links.linkedin ? `<a href="${this.escapeHtml(instructor.social_links.linkedin)}" target="_blank" class="share-icon-btn"><i class="fab fa-linkedin-in"></i></a>` : ''}
                        ${instructor.social_links.github ? `<a href="${this.escapeHtml(instructor.social_links.github)}" target="_blank" class="share-icon-btn"><i class="fab fa-github"></i></a>` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    populateReviewsTab() {
        if (!this.reviewsData) return;

        const container = document.getElementById('tabReviews');
        if (!container) return;

        const data = this.reviewsData;

        container.innerHTML = `
            <div class="reviews-summary-bar">
                <div class="reviews-avg">
                    <span class="reviews-avg-score">${this.escapeHtml(String(this.courseData.rating))}</span>
                    <div class="reviews-stars-display">${this.generateStars(this.courseData.rating)}</div>
                    <span class="reviews-total">${this.escapeHtml(String(data.total_reviews))} reviews</span>
                </div>
                <div class="reviews-distribution">
                    ${[5, 4, 3, 2, 1].map(star => `
                        <div class="review-dist-row">
                            <span>${star} Stars</span>
                            <div class="dist-bar-bg">
                                <div class="dist-bar-fill" style="width:${data.distribution[star]}%"></div>
                            </div>
                            <span>${data.distribution[star]}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            ${this.isEnrolled ? `
                <div id="reviewForm" style="margin: 2rem 0; padding: 1.5rem; background: #F9FAFB; border-radius: 12px;">
                    <h4 style="margin-bottom: 1rem;">Write a Review</h4>
                    <div style="margin-bottom: 1rem;">
                        <span style="margin-right: 0.5rem;">Your Rating:</span>
                        ${[1,2,3,4,5].map(star => `
                            <i class="far fa-star rating-star" data-rating="${star}"
                               style="cursor: pointer; font-size: 1.25rem; color: #F59E0B; margin: 0 2px;"
                               onclick="courseDetailPage.setRating(${star})"
                               onmouseover="courseDetailPage.highlightStars(${star})"
                               onmouseout="courseDetailPage.resetStars()"></i>
                        `).join('')}
                    </div>
                    <textarea id="reviewComment" placeholder="Share your experience with this course..."
                              style="width: 100%; padding: 0.75rem; border: 1px solid #D1D5DB; border-radius: 8px; margin-bottom: 1rem; min-height: 100px; font-family: inherit;"></textarea>
                    <button onclick="courseDetailPage.submitReview()" class="enroll-btn-primary" style="width: auto; padding: 0.75rem 2rem;">
                        Submit Review
                    </button>
                </div>
            ` : (this.userAuth?.is_authenticated ? `
                <div style="margin: 2rem 0; padding: 1.5rem; background: #F9FAFB; border-radius: 12px; text-align: center;">
                    <p style="color: #6B7280;"><i class="fas fa-lock"></i> Enroll in this course to write a review.</p>
                </div>
            ` : `
                <div style="margin: 2rem 0; padding: 1.5rem; background: #F9FAFB; border-radius: 12px; text-align: center;">
                    <p style="color: #6B7280;">Please <a href="/login" style="color: #8B5CF6;">log in</a> to write a review.</p>
                </div>
            `)}

            <div class="reviews-list" id="reviewsList">
                ${data.items.map(review => this.createReviewCard(review)).join('')}
            </div>

            ${data.current_page < data.total_pages ? `
                <div style="text-align: center; margin-top: 2rem;">
                    <button class="load-more-reviews-btn" id="loadMoreReviewsBtn" onclick="courseDetailPage.loadMoreReviews()">
                        Show More Reviews <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
            ` : ''}
        `;

        this.updateReviewTabCount();
        this.bindHelpfulButtons();
        this.bindDropdownButtons();
    }

    createReviewCard(review) {
        const formattedDate = review.created_at && review.created_at.includes('T')
            ? formatDateTime(review.created_at)
            : review.created_at;

        const hasLiked = review.user_has_liked || false;
        const thumbIcon = hasLiked ? 'fas' : 'far';
        const thumbClass = hasLiked ? 'helpful-btn-liked' : 'helpful-btn';

        const isOwner = review.is_owner || (this.userAuth && this.userAuth.user_id && review.user_id === this.userAuth.user_id);

        return `
            <div class="review-card-pub" data-review-id="${review.id}" style="position: relative;">
                <div class="review-card-header">
                    <img src="${this.escapeHtml(review.user_avatar)}" alt="${this.escapeHtml(review.user_name)}" class="review-avatar">
                    <div>
                        <strong>${this.escapeHtml(review.user_name)}</strong>
                        <div class="review-stars-sm">${this.generateStars(review.rating)}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="review-time">${this.escapeHtml(formattedDate)}</span>
                        ${isOwner ? `
                            <div style="position: relative;">
                                <button class="review-three-dot-btn" data-review-id="${review.id}" title="More options" style="background: none; border: none; cursor: pointer; color: #6B7280; font-size: 1.25rem; padding: 4px 8px; border-radius: 4px; transition: all 0.2s;" onclick="courseDetailPage.toggleDropdown(event, ${review.id})" onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='none'">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <div class="review-dropdown-menu" id="dropdown-${review.id}" style="display: none; position: absolute; right: 0; top: 100%; background: white; border: 1px solid #E5E7EB; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 1000; min-width: 150px; padding: 4px 0;">
                                    <button class="dropdown-item delete-item" data-review-id="${review.id}" style="display: flex; align-items: center; gap: 8px; width: 100%; padding: 8px 16px; border: none; background: none; cursor: pointer; color: #EF4444; font-size: 0.875rem; transition: background 0.2s;" onmouseover="this.style.background='#FEF2F2'" onmouseout="this.style.background='none'">
                                        <i class="fas fa-trash-alt"></i> Remove
                                    </button>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <p class="review-text">${this.escapeHtml(review.comment)}</p>
                <div class="review-footer">
                    <button class="${thumbClass}" data-review-id="${review.id}" ${!this.userAuth?.is_authenticated ? 'disabled' : ''}>
                        <i class="${thumbIcon} fa-thumbs-up"></i>
                        <span class="helpful-count">${review.helpful_count}</span> found helpful
                    </button>
                    ${review.is_verified_purchase ? '<span class="verified-purchase-badge"><i class="fas fa-check-circle"></i> Verified Purchase</span>' : ''}
                </div>
            </div>
        `;
    }

    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let stars = '';
        for (let i = 0; i < fullStars; i++) stars += '⭐';
        if (hasHalfStar) stars += '✨';
        return stars;
    }

    updateTabCounts() {
        const curriculumTab = document.querySelector('.detail-tab[data-tab="curriculum"] .tab-count');
        if (curriculumTab && this.curriculumData) {
            const totalLessons = this.curriculumData.reduce((sum, section) => sum + (section.lessons_count || section.lessons?.length || 0), 0);
            curriculumTab.textContent = totalLessons;
        }

        this.updateReviewTabCount();
    }

    updateReviewTabCount() {
        const reviewsTab = document.querySelector('.detail-tab[data-tab="reviews"] .tab-count');
        if (reviewsTab && this.reviewsData) {
            reviewsTab.textContent = this.reviewsData.total_reviews || 0;
        }
    }

    bindHelpfulButtons() {
        const helpfulButtons = document.querySelectorAll('.helpful-btn, .helpful-btn-liked');
        helpfulButtons.forEach(button => {
            button.removeEventListener('click', this.handleHelpfulClick);
            button.addEventListener('click', (e) => this.handleHelpfulClick(e));
        });
    }

    bindDropdownButtons() {
        const deleteItems = document.querySelectorAll('.dropdown-item.delete-item');
        deleteItems.forEach(item => {
            item.removeEventListener('click', this.handleDeleteFromDropdown);
            item.addEventListener('click', (e) => this.handleDeleteFromDropdown(e));
        });
    }

    toggleDropdown(event, reviewId) {
        event.stopPropagation();
        this.closeAllDropdowns();

        const dropdown = document.getElementById(`dropdown-${reviewId}`);
        if (dropdown) {
            dropdown.style.display = 'block';
            this.activeDropdown = dropdown;
        }
    }

    handleDeleteFromDropdown(e) {
        e.preventDefault();
        e.stopPropagation();

        const button = e.currentTarget;
        const reviewId = parseInt(button.dataset.reviewId);

        if (!reviewId) return;

        this.closeAllDropdowns();
        this.showDeleteConfirmation(reviewId);
    }

    handleHelpfulClick(e) {
        e.preventDefault();
        e.stopPropagation();

        const button = e.currentTarget;
        const reviewId = parseInt(button.dataset.reviewId);

        if (!reviewId) return;

        if (!this.userAuth || !this.userAuth.is_authenticated) {
            const currentUrl = encodeURIComponent(window.location.pathname);
            this.showToast('Please log in to like reviews', 'info');
            setTimeout(() => {
                window.location.href = baseUrl + `/account/auth/login?next=${currentUrl}`;
            }, 1000);
            return;
        }

        if (this.processingHelpfulReviews.has(reviewId)) return;

        this.processingHelpfulReviews.add(reviewId);

        const currentLiked = button.classList.contains('helpful-btn-liked');
        const countSpan = button.querySelector('.helpful-count');
        const currentCount = parseInt(countSpan.textContent);
        const icon = button.querySelector('i');

        if (currentLiked) {
            button.classList.remove('helpful-btn-liked');
            button.classList.add('helpful-btn');
            icon.classList.remove('fas');
            icon.classList.add('far');
            countSpan.textContent = currentCount - 1;
        } else {
            button.classList.remove('helpful-btn');
            button.classList.add('helpful-btn-liked');
            icon.classList.remove('far');
            icon.classList.add('fas');
            countSpan.textContent = currentCount + 1;
        }

        this.toggleHelpful(reviewId, button, currentCount, currentLiked);
    }

    async toggleHelpful(reviewId, button, originalCount, wasLiked) {
        try {
            const result = await CourseApiService.toggleReviewHelpful(this.courseId, reviewId);

            if (result.helpful_count !== undefined) {
                const countSpan = button.querySelector('.helpful-count');
                countSpan.textContent = result.helpful_count;
            }

            if (result.user_has_liked !== undefined) {
                const icon = button.querySelector('i');
                if (result.user_has_liked) {
                    button.classList.remove('helpful-btn');
                    button.classList.add('helpful-btn-liked');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    this.showToast('Marked as helpful 👍');
                } else {
                    button.classList.remove('helpful-btn-liked');
                    button.classList.add('helpful-btn');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    this.showToast('Removed helpful mark');
                }
            }

            if (this.reviewsData && this.reviewsData.items) {
                const review = this.reviewsData.items.find(r => r.id === reviewId);
                if (review) {
                    review.user_has_liked = result.user_has_liked !== undefined ? result.user_has_liked : !wasLiked;
                    review.helpful_count = result.helpful_count !== undefined ? result.helpful_count : review.helpful_count;
                }
            }
        } catch (error) {
            console.error('Failed to toggle helpful:', error);
            this.showToast('Failed to update. Please try again.', 'error');

            const countSpan = button.querySelector('.helpful-count');
            const icon = button.querySelector('i');
            countSpan.textContent = originalCount;

            if (wasLiked) {
                button.classList.remove('helpful-btn');
                button.classList.add('helpful-btn-liked');
                icon.classList.remove('far');
                icon.classList.add('fas');
            } else {
                button.classList.remove('helpful-btn-liked');
                button.classList.add('helpful-btn');
                icon.classList.remove('fas');
                icon.classList.add('far');
            }
        } finally {
            this.processingHelpfulReviews.delete(reviewId);
        }
    }

    showDeleteConfirmation(reviewId) {
        const existingDialog = document.querySelector('.delete-confirmation-dialog');
        if (existingDialog) existingDialog.remove();

        const dialog = document.createElement('div');
        dialog.className = 'delete-confirmation-dialog';
        dialog.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.5); z-index: 10002;
            display: flex; align-items: center; justify-content: center; padding: 2rem;
        `;

        dialog.innerHTML = `
            <div style="background: white; border-radius: 16px; max-width: 400px; width: 100%; padding: 2rem; text-align: center;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #F59E0B; margin-bottom: 1rem;"></i>
                <h3 style="margin: 0 0 0.5rem 0;">Delete Review</h3>
                <p style="color: #6B7280; margin-bottom: 1.5rem;">Are you sure you want to delete your review? This action cannot be undone.</p>
                <div style="display: flex; gap: 10px;">
                    <button id="cancelDeleteBtn" style="flex: 1; background: #E5E7EB; color: #374151; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 500;">
                        Cancel
                    </button>
                    <button id="confirmDeleteBtn" style="flex: 1; background: #EF4444; color: white; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 500;">
                        Delete
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
            dialog.remove();
        });

        document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
            dialog.remove();
            await this.deleteReview(reviewId);
        });

        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });

        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                dialog.remove();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    async deleteReview(reviewId) {
        if (this.processingDeleteReviews.has(reviewId)) return;

        this.processingDeleteReviews.add(reviewId);

        const reviewCard = document.querySelector(`.review-card-pub[data-review-id="${reviewId}"]`);
        if (reviewCard) {
            reviewCard.style.opacity = '0.5';
            reviewCard.style.pointerEvents = 'none';
        }

        try {
            await CourseApiService.deleteReview(this.courseId, reviewId);

            if (this.reviewsData && this.reviewsData.items) {
                this.reviewsData.items = this.reviewsData.items.filter(r => r.id !== reviewId);
                this.reviewsData.total_reviews = Math.max(0, (this.reviewsData.total_reviews || 1) - 1);
            }

            if (reviewCard) {
                reviewCard.style.transition = 'all 0.3s ease';
                reviewCard.style.maxHeight = reviewCard.offsetHeight + 'px';
                reviewCard.style.opacity = '0';
                reviewCard.style.transform = 'scale(0.95)';
                reviewCard.style.marginBottom = '0';
                reviewCard.style.padding = '0';

                setTimeout(() => {
                    reviewCard.remove();
                }, 300);
            }

            this.showToast('Review deleted successfully 🗑️');
            this.updateReviewTabCount();

        } catch (error) {
            console.error('Failed to delete review:', error);
            this.showToast('Failed to delete review. Please try again.', 'error');

            if (reviewCard) {
                reviewCard.style.opacity = '1';
                reviewCard.style.pointerEvents = '';
                reviewCard.style.transform = '';
                reviewCard.style.maxHeight = '';
                reviewCard.style.marginBottom = '';
                reviewCard.style.padding = '';
            }
        } finally {
            this.processingDeleteReviews.delete(reviewId);
        }
    }

    async loadMoreReviews() {
        if (this.isLoadingMoreReviews) return;

        this.isLoadingMoreReviews = true;
        const loadBtn = document.getElementById('loadMoreReviewsBtn');
        if (loadBtn) {
            loadBtn.disabled = true;
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        }

        try {
            this.currentReviewPage++;
            const moreReviews = await CourseApiService.fetchReviews(this.courseId, this.currentReviewPage, 3);

            if (this.userAuth && this.userAuth.is_authenticated && moreReviews.items) {
                moreReviews.items = moreReviews.items.map(review => ({
                    ...review,
                    is_owner: review.user_id === this.userAuth.user_id
                }));
            }

            if (this.reviewsData && moreReviews.items) {
                this.reviewsData.items = [...this.reviewsData.items, ...moreReviews.items];
                this.reviewsData.current_page = moreReviews.current_page || this.currentReviewPage;
                this.reviewsData.total_pages = moreReviews.total_pages || this.reviewsData.total_pages;
            }

            const reviewsList = document.getElementById('reviewsList');
            if (reviewsList && moreReviews.items) {
                reviewsList.innerHTML += moreReviews.items.map(review => this.createReviewCard(review)).join('');
            }

            this.bindHelpfulButtons();
            this.bindDropdownButtons();

            if (moreReviews.current_page >= moreReviews.total_pages) {
                const loadMoreContainer = loadBtn?.parentElement;
                if (loadMoreContainer) loadMoreContainer.remove();
            } else if (loadBtn) {
                loadBtn.disabled = false;
                loadBtn.innerHTML = 'Show More Reviews <i class="fas fa-chevron-down"></i>';
            }
        } catch (error) {
            console.error('Failed to load more reviews:', error);
            this.showToast('Failed to load reviews. Please try again.', 'error');
            if (loadBtn) {
                loadBtn.disabled = false;
                loadBtn.innerHTML = 'Show More Reviews <i class="fas fa-chevron-down"></i>';
            }
        } finally {
            this.isLoadingMoreReviews = false;
        }
    }

    setRating(rating) {
        this.currentRating = rating;
        this.highlightStars(rating);
    }

    highlightStars(rating) {
        const stars = document.querySelectorAll('.rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.remove('far');
                star.classList.add('fas');
            } else {
                star.classList.remove('fas');
                star.classList.add('far');
            }
        });
    }

    resetStars() {
        if (this.currentRating) {
            this.highlightStars(this.currentRating);
        } else {
            const stars = document.querySelectorAll('.rating-star');
            stars.forEach(star => {
                star.classList.remove('fas');
                star.classList.add('far');
            });
        }
    }

    async submitReview() {
        if (!this.currentRating) {
            this.showToast('Please select a rating', 'warning');
            return;
        }

        const comment = document.getElementById('reviewComment')?.value.trim();
        if (!comment) {
            this.showToast('Please write a review', 'warning');
            return;
        }

        try {
            await CourseApiService.submitReview(this.courseId, this.currentRating, comment);
            this.showToast('Review submitted successfully! 🎉');

            document.getElementById('reviewComment').value = '';
            this.currentRating = null;
            this.resetStars();

            this.currentReviewPage = 1;
            this.reviewsData = await CourseApiService.fetchReviews(this.courseId, 1, 3);

            this.populateReviewsTab();
            this.updateReviewTabCount();
        } catch (error) {
            console.error('Failed to submit review:', error);
            this.showToast('Failed to submit review. Please try again.', 'error');
        }
    }

    async handleEnrollClick() {
        // Check if user is instructor
        if (this.userAuth && this.userAuth.is_instructor) {
            this.showToast('Instructors cannot enroll in courses', 'info');
            return;
        }

        if (!this.userAuth || !this.userAuth.is_authenticated) {
            const currentUrl = encodeURIComponent(window.location.pathname);
            this.showToast('Please log in to enroll in this course', 'info');
            setTimeout(() => {
                window.location.href = baseUrl + `/account/auth/login?next=${currentUrl}&action=enroll`;
            }, 1000);
            return;
        }

        if (this.isEnrolling) return;

        this.isEnrolling = true;
        const enrollBtn = document.getElementById('enrollBtn');

        if (enrollBtn) {
            enrollBtn.disabled = true;
            enrollBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }

        try {
            // Check if the course is free
            const coursePrice = parseFloat(this.courseData?.price) || 0;

            if (coursePrice === 0) {
                // Free course - enroll directly

                const enrollData = await CourseApiService.enrollInCourse(this.courseId);

                if (enrollData) {
                    this.isEnrolled = true;

                    this.enrollment_id = enrollData.enrollment_id
                    this.showToast('Successfully enrolled in course! 🎉');
                    this.updateEnrollmentCard();
                    this.populateCurriculumTab();
                    this.populateReviewsTab();
                } else {
                    throw new Error('Enrollment failed');
                }
            } else {
                // Paid course - first enroll, then redirect to checkout
                const enrollData = await CourseApiService.enrollInCourse(this.courseId);

                if (enrollData && enrollData.enrollment_id) {
                    // Create checkout session
                    const checkoutData = await CourseApiService.createEnrollmentCheckout(enrollData.enrollment_id);

                    if (checkoutData && checkoutData.checkout_url) {
                        // Redirect to checkout page
                        window.location.href = checkoutData.checkout_url;
                    } else {
                        throw new Error('Failed to create checkout session');
                    }
                } else {
                    throw new Error('Failed to create enrollment');
                }
            }
        } catch (error) {
            console.error('Failed to enroll:', error);
            this.showToast('Failed to process enrollment. Please try again.', 'error');

            if (enrollBtn) {
                enrollBtn.disabled = false;
                enrollBtn.innerHTML = '<i class="fas fa-rocket"></i> Enroll Now';
            }
        } finally {
            this.isEnrolling = false;
        }
    }

    handleWishlistClick() {
        // Check if user is instructor
        if (this.userAuth && this.userAuth.is_instructor) {
            this.showToast('Instructors cannot add courses to wishlist', 'info');
            return;
        }

        if (!this.userAuth || !this.userAuth.is_authenticated) {
            const currentUrl = encodeURIComponent(window.location.pathname);
            this.showToast('Please log in to add courses to your wishlist', 'info');
            setTimeout(() => {
                window.location.href = baseUrl + `/account/auth/login?next=${currentUrl}&action=wishlist`;
            }, 1000);
            return;
        }

        this.toggleWishlist();
    }

    bindEvents() {
        document.querySelectorAll('.detail-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        document.getElementById('enrollBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleEnrollClick();
        });

        document.getElementById('wishlistBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleWishlistClick();
        });
    }

    switchTab(tabName) {
        this.activeTab = tabName;

        document.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
        const activeTab = document.querySelector(`.detail-tab[data-tab="${tabName}"]`);
        if (activeTab) activeTab.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        const target = document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
        if (target) target.style.display = '';

        if (window.innerWidth < 768) {
            document.getElementById('detailTabs')?.scrollIntoView({ behavior: 'smooth' });
        }
    }

    previewLesson(sectionIndex, lessonIndex) {
        const section = this.curriculumData[sectionIndex];
        if (!section || !section.lessons) return;

        const lesson = section.lessons[lessonIndex];
        if (!lesson || !lesson.is_previewable) return;

        this.switchTab('curriculum');

        setTimeout(() => {
            const sectionElement = document.querySelector(`.curriculum-section[data-section-index="${sectionIndex}"]`);
            if (sectionElement) {
                const sectionHeader = sectionElement.querySelector('.curriculum-section-header');
                if (sectionHeader && !sectionHeader.classList.contains('open')) {
                    toggleCurriculumSection(sectionHeader);
                }

                const lessonElements = sectionElement.querySelectorAll('.curriculum-lesson');
                const lessonElement = lessonElements[lessonIndex];
                if (lessonElement) {
                    lessonElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    lessonElement.style.background = '#F3F4F6';
                    setTimeout(() => { lessonElement.style.background = ''; }, 2000);
                }
            }

            this.showPreviewModal(lesson);
        }, 300);
    }

    showPreviewModal(lesson) {
        const existingModal = document.querySelector('.preview-modal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.className = 'preview-modal';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.9); z-index: 10001;
            display: flex; align-items: center; justify-content: center; padding: 2rem;
        `;

        const hasVideo = lesson.video_url && lesson.type === 'video';

        modal.innerHTML = `
            <div style="background: white; border-radius: 16px; max-width: 900px; width: 100%; overflow: hidden; max-height: 90vh;">
                <div style="padding: 1.5rem; border-bottom: 1px solid #E5E7EB; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 1.25rem;">Preview: ${this.escapeHtml(lesson.title)}</h3>
                    <button onclick="this.closest('.preview-modal').remove(); courseDetailPage.stopVideo();"
                            style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #6B7280; padding: 0.5rem;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div style="background: #000; position: relative; ${hasVideo ? '' : 'min-height: 400px; display: flex; align-items: center; justify-content: center;'}">
                    ${hasVideo ? `
                        <video id="previewVideoPlayer" controls autoplay style="width: 100%; max-height: 60vh;" controlsList="nodownload">
                            <source src="${this.escapeHtml(lesson.video_url)}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    ` : `
                        <div style="color: white; text-align: center; padding: 3rem;">
                            <i class="fas fa-${lesson.type === 'article' ? 'file-alt' : lesson.type === 'quiz' ? 'question-circle' : 'play-circle'}" style="font-size: 4rem; margin-bottom: 1rem;"></i>
                            <p style="font-size: 1.25rem;">Preview Content</p>
                            <p style="color: #9CA3AF;">${lesson.type.charAt(0).toUpperCase() + lesson.type.slice(1)} · Duration: ${this.escapeHtml(lesson.duration)}</p>
                        </div>
                    `}
                </div>
                <div style="padding: 1.5rem; background: #F9FAFB;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <div>
                            <p style="margin: 0; font-weight: 600; color: #1F2937;">${this.escapeHtml(lesson.title)}</p>
                            <p style="margin: 0.25rem 0 0 0; color: #6B7280; font-size: 0.875rem;">
                                <i class="far fa-clock"></i> ${this.escapeHtml(lesson.duration)}
                            </p>
                        </div>
                        <span style="background: #FEF3C7; color: #92400E; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                            <i class="fas fa-eye"></i> FREE PREVIEW
                        </span>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button onclick="this.closest('.preview-modal').remove(); courseDetailPage.stopVideo();"
                                style="flex: 1; background: #6B7280; color: white; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 500;">
                            Close Preview
                        </button>
                        ${!this.isEnrolled && !(this.userAuth && this.userAuth.is_instructor) ? `
                            <button onclick="this.closest('.preview-modal').remove(); courseDetailPage.stopVideo(); courseDetailPage.handleEnrollClick();"
                                    style="flex: 1; background: #8B5CF6; color: white; border: none; padding: 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 500;">
                                <i class="fas fa-rocket"></i> Enroll Now
                            </button>
                        ` : ''}
                    </div>
                    ${!this.isEnrolled && !(this.userAuth && this.userAuth.is_instructor) ? `
                        <p style="text-align: center; margin-top: 1rem; color: #6B7280; font-size: 0.875rem;">
                            <i class="fas fa-lock"></i> Enroll to access the full course content
                        </p>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        if (hasVideo) {
            setTimeout(() => {
                this.currentVideoPlayer = document.getElementById('previewVideoPlayer');
            }, 100);
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.stopVideo();
                modal.remove();
            }
        });

        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.stopVideo();
                modal.remove();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    stopVideo() {
        if (this.currentVideoPlayer) {
            this.currentVideoPlayer.pause();
            this.currentVideoPlayer.currentTime = 0;
            this.currentVideoPlayer = null;
        }
    }

    playPreview() {
        this.switchTab('curriculum');

        setTimeout(() => {
            const tabCurriculum = document.getElementById('tabCurriculum');
            if (tabCurriculum) {
                tabCurriculum.scrollIntoView({ behavior: 'smooth' });
            }

            let foundPreview = false;
            const sections = document.querySelectorAll('.curriculum-section');

            for (let i = 0; i < sections.length; i++) {
                const section = sections[i];
                const sectionIndex = parseInt(section.dataset.sectionIndex);
                const sectionData = this.curriculumData[sectionIndex];

                if (sectionData && sectionData.lessons) {
                    const hasPreview = sectionData.lessons.some(l => l.is_previewable);
                    if (hasPreview) {
                        const sectionHeader = section.querySelector('.curriculum-section-header');
                        if (sectionHeader) {
                            sectionHeader.classList.add('open');
                            const lessonsDiv = sectionHeader.nextElementSibling;
                            if (lessonsDiv) lessonsDiv.style.display = '';
                        }
                        foundPreview = true;
                        break;
                    }
                }
            }

            if (foundPreview) {
                this.showToast('Preview lessons are now visible. Look for "Preview" labels.');
            } else {
                this.showToast('No preview lessons available in this course.');
            }
        }, 300);
    }

    async toggleWishlist() {
        const btn = document.getElementById('wishlistBtn');

        try {
            const result = await CourseApiService.toggleWishlist(this.courseId);
            this.isWishlisted = result.is_wishlisted;

            if (this.isWishlisted) {
                btn.innerHTML = '<i class="fas fa-heart"></i> Saved to Wishlist';
                btn.classList.add('wishlisted');
                this.showToast('Course added to wishlist ❤️');
            } else {
                btn.innerHTML = '<i class="far fa-heart"></i> Add to Wishlist';
                btn.classList.remove('wishlisted');
                this.showToast('Course removed from wishlist');
            }
        } catch (error) {
            console.error('Failed to toggle wishlist:', error);
            this.showToast('Failed to update wishlist', 'error');
        }
    }

    shareCourse(platform) {
        const url = window.location.href;
        const title = this.courseData?.title || 'Course';
        const text = `I found this amazing course: ${title}`;

        const urls = {
            facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
            twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
            linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`
        };

        if (urls[platform]) {
            window.open(urls[platform], '_blank', 'width=600,height=400');
        }
    }

    copyCourseLink() {
        navigator.clipboard.writeText(window.location.href).then(() => {
            this.showToast('Link copied! 📋');
        });
    }

    showToast(message, type = 'success') {
        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#3B82F6'
        };

        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: #1F2937; color: #FFF; padding: 12px 24px; border-radius: 8px;
            font-size: 0.875rem; z-index: 9999; box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            display: flex; align-items: center; gap: 8px;
            border-left: 4px solid ${colors[type] || colors.success};
        `;

        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        toast.innerHTML = `
            <i class="fas fa-${icons[type] || icons.success}" style="color: ${colors[type] || colors.success};"></i>
            ${message}
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }
}

// ==================== GLOBAL FUNCTIONS ====================
function toggleCurriculumSection(header) {
    header.classList.toggle('open');
    const lessons = header.nextElementSibling;
    if (lessons) {
        lessons.style.display = lessons.style.display === 'none' ? '' : 'none';
    }
}

// ==================== INITIALIZATION ====================
let courseDetailPage;
document.addEventListener('DOMContentLoaded', () => {
    courseDetailPage = new CourseDetailPage();
    window.courseDetailPage = courseDetailPage;
});

window.toggleCurriculumSection = toggleCurriculumSection;
