// ============================================
// COURSE CATALOG PAGE CONTROLLER
// ============================================

const filtersLoader = new FiltersLoader({
    containerId: 'catalogFilters',
    includeSubcategories: true, // Changed from includeSubcategories to includeCategories
    // filtersEndpoint: '/api/catalog/filters/' // Uncomment for production
});

class CourseCatalogPage {
    constructor() {
        this.activeCategory = 'all';
        this.searchQuery = '';
        // ADDED: category to activeFilters
        this.activeFilters = { category: [], rating: [], level: [], price: [], duration: [], language: ['en'], subcategory: [] };
        this.sortBy = 'popular';
        this.currentPage = 1;
        this.perPage = 12;
        this.totalResults = 0;
        this.totalPages = 0;
        this.currentCourses = [];
        this.isLoading = false;
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.fetchCourses();
    }

    bindEvents() {
        // REMOVED: Category pills event listeners (no longer needed with filter categories)
        // If you still have cat-pills elsewhere, keep this, otherwise remove:
        // document.querySelectorAll('.cat-pill')...

        // Search with debounce
        const searchInput = document.getElementById('catalogSearch');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.searchQuery = e.target.value.toLowerCase().trim();
                    this.currentPage = 1;
                    this.fetchCourses();
                }, 500);
            });
        }

        // Sort
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.currentPage = 1;
                this.fetchCourses();
            });
        }

        // REMOVED: Individual filter checkbox listeners - now handled by FiltersLoader events
        // Instead, listen for custom events from FiltersLoader

        // Listen for filter changes from FiltersLoader
        document.addEventListener('filtersChanged', (e) => {
            if (e.detail.containerId === 'catalogFilters') {
                this.collectActiveFilters();
                this.currentPage = 1;
                this.fetchCourses();
            }
        });

        // Listen for filter clear from FiltersLoader
        document.addEventListener('filtersCleared', (e) => {
            if (e.detail.containerId === 'catalogFilters') {
                this.activeFilters = { category: [], rating: [], level: [], price: [], duration: [], language: [], subcategory: [] };
                this.currentPage = 1;
                this.fetchCourses();
            }
        });

        // Pagination
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        if (prevBtn) prevBtn.addEventListener('click', () => this.changePage(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.changePage(1));
    }

    collectActiveFilters() {
        // UPDATED: Include category filter
        this.activeFilters = { category: [], rating: [], level: [], price: [], duration: [], language: [], subcategory: [] };
        document.querySelectorAll('.filter-input:checked').forEach(cb => {
            const filterType = cb.dataset.filter;
            if (this.activeFilters[filterType]) {
                this.activeFilters[filterType].push(cb.value);
            }
        });
    }

    buildApiParams() {
        const params = new URLSearchParams();

        // Pagination params
        params.append('page', this.currentPage);
        params.append('per_page', this.perPage);

        // Search query
        if (this.searchQuery) {
            params.append('search', this.searchQuery);
        }

        // Sort
        params.append('sort', this.sortBy);

        // ADDED: Category filter
        if (this.activeFilters.category.length > 0) {
            this.activeFilters.category.forEach(cat => {
                params.append('category', cat);
            });
        }

        // Filters
        if (this.activeFilters.rating.length > 0) {
            const minRating = Math.min(...this.activeFilters.rating.map(Number));
            params.append('min_rating', minRating);
        }

        if (this.activeFilters.level.length > 0) {
            this.activeFilters.level.forEach(level => {
                params.append('level', level);
            });
        }

        if (this.activeFilters.price.length === 1) {
            params.append('price_type', this.activeFilters.price[0]);
        }

        if (this.activeFilters.duration.length > 0) {
            this.activeFilters.duration.forEach(duration => {
                params.append('duration', duration);
            });
        }

        if (this.activeFilters.language.length > 0) {
            this.activeFilters.language.forEach(lang => {
                params.append('language', lang);
            });
        }

        if (this.activeFilters.subcategory.length > 0) {
            this.activeFilters.subcategory.forEach(sub => {
                console.log(sub)
                params.append('subcategory', sub);
            });
        }

        return params;
    }
    mapData(courses){
        const payloads = [];
        courses.forEach(course => {
            const { rating_count, original_price, ...rest } = course;
            const payload = {
                ...rest,
                ratingCount:rating_count,
                originalPrice:original_price
            };
            payloads.push(payload);
        });
        return payloads;
    }
    async fetchCourses() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const params = this.buildApiParams();

            // ==========================================
            // REAL API CALL - Uncomment for production
            // ==========================================
            // const response = await fetch(`/api/courses/?${params.toString()}`);
            // const data = await response.json();
            // this.currentCourses = data.results || data.courses || [];
            // this.totalResults = data.total || data.count || 0;
            // this.totalPages = data.total_pages || Math.ceil(this.totalResults / this.perPage);
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/courses/?${params.toString()}`,
                {
                    method: "GET",
                }
            );
            const data = await response.json();
            this.currentCourses = this.mapData(data.results);
            console.log(this.currentCourses)
            this.totalResults = data.total || data.count || 0;
            this.totalPages = data.total_pages || Math.ceil(this.totalResults / this.perPage);
            // ==========================================
            // DUMMY DATA (simulates API response)
            // ==========================================
            // await new Promise(r => setTimeout(r, 400));
            // const dummyResponse = this.getDummyApiResponse();
            // this.currentCourses = dummyResponse.courses;
            // this.totalResults = dummyResponse.total;
            // this.totalPages = Math.ceil(this.totalResults / this.perPage);

            this.renderAll();
        } catch (error) {
            console.error('Error fetching courses:', error);
            this.showError('Failed to load courses. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    getDummyApiResponse() {
        const allCourses = this.getAllDummyCourses();
        let filtered = this.filterCoursesServerSide(allCourses);

        const total = filtered.length;
        const start = (this.currentPage - 1) * this.perPage;
        const courses = filtered.slice(start, start + this.perPage);

        return {
            courses: courses,
            total: total,
            page: this.currentPage,
            per_page: this.perPage
        };
    }

    filterCoursesServerSide(courses) {
        let filtered = [...courses];

        // UPDATED: Filter by category if selected in filters
        if (this.activeFilters.category.length > 0) {
            filtered = filtered.filter(c => this.activeFilters.category.includes(c.category));
        }

        if (this.searchQuery) {
            filtered = filtered.filter(c =>
                c.title.toLowerCase().includes(this.searchQuery) ||
                c.instructor.toLowerCase().includes(this.searchQuery) ||
                c.category.toLowerCase().includes(this.searchQuery)
            );
        }

        if (this.activeFilters.rating.length > 0) {
            const minRating = Math.min(...this.activeFilters.rating.map(Number));
            filtered = filtered.filter(c => c.rating >= minRating);
        }

        if (this.activeFilters.level.length > 0) {
            filtered = filtered.filter(c => this.activeFilters.level.includes(c.level));
        }

        if (this.activeFilters.price.length === 1) {
            if (this.activeFilters.price[0] === 'free') {
                filtered = filtered.filter(c => c.price === 0);
            } else if (this.activeFilters.price[0] === 'paid') {
                filtered = filtered.filter(c => c.price > 0);
            }
        }

        if (this.activeFilters.duration.length > 0) {
            filtered = filtered.filter(c => {
                const hours = parseInt(c.duration);
                for (const d of this.activeFilters.duration) {
                    if (d === 'short' && hours <= 3) return true;
                    if (d === 'medium' && hours > 3 && hours <= 10) return true;
                    if (d === 'long' && hours > 10) return true;
                }
                return false;
            });
        }

        if (this.activeFilters.language.length > 0) {
            filtered = filtered.filter(c => this.activeFilters.language.includes(c.language));
        }

        if (this.activeFilters.subcategory.length > 0) {
            // Filter out "all-{category}" values before filtering
            const validSubs = this.activeFilters.subcategory.filter(s => !s.startsWith('all-'));
            if (validSubs.length > 0) {
                filtered = filtered.filter(c => validSubs.includes(c.subcategory));
            }
        }

        // Sort
        switch (this.sortBy) {
            case 'popular':
                filtered.sort((a, b) => b.students - a.students);
                break;
            case 'rating':
                filtered.sort((a, b) => b.rating - a.rating);
                break;
            case 'price-asc':
                filtered.sort((a, b) => a.price - b.price);
                break;
            case 'price-desc':
                filtered.sort((a, b) => b.price - a.price);
                break;
        }

        return filtered;
    }

    getAllDummyCourses() {
        return [
            { id: 1, title: 'Python for Data Science', instructor: 'Dr. Sarah Chen', category: 'data-science', subcategory: 'python', rating: 4.8, ratingCount: 2450, students: 12450, level: 'intermediate', duration: '42h', price: 49.99, originalPrice: 79.99, language: 'en', badge: 'bestseller', thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=600&h=340&fit=crop', slug: 'python-data-science' },
            { id: 2, title: 'Machine Learning A-Z', instructor: 'Kirill Eremenko', category: 'data-science', subcategory: 'machine-learning', rating: 4.6, ratingCount: 1800, students: 8900, level: 'beginner', duration: '38h', price: 54.99, originalPrice: 89.99, language: 'en', badge: 'bestseller', thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=340&fit=crop', slug: 'ml-az' },
            { id: 3, title: 'Deep Learning Specialization', instructor: 'Andrew Ng', category: 'data-science', subcategory: 'machine-learning', rating: 4.9, ratingCount: 3100, students: 15000, level: 'advanced', duration: '56h', price: 0, originalPrice: null, language: 'en', badge: 'new', thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=340&fit=crop', slug: 'deep-learning' },
            { id: 4, title: 'Full-Stack Web Development Bootcamp', instructor: 'Mike Johnson', category: 'programming', subcategory: 'web-development', rating: 4.5, ratingCount: 2100, students: 18000, level: 'beginner', duration: '52h', price: 59.99, originalPrice: 99.99, language: 'en', badge: 'bestseller', thumbnail: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=600&h=340&fit=crop', slug: 'fullstack-bootcamp' },
            { id: 5, title: 'Advanced JavaScript Concepts', instructor: 'Alex Rivera', category: 'programming', subcategory: 'web-development', rating: 4.7, ratingCount: 890, students: 5600, level: 'advanced', duration: '28h', price: 44.99, originalPrice: 69.99, language: 'en', badge: null, thumbnail: 'https://images.unsplash.com/photo-1579468118864-1b9ea3c0db4a?w=600&h=340&fit=crop', slug: 'advanced-js' },
            { id: 6, title: 'UI/UX Design Masterclass', instructor: 'Priya Patel', category: 'design', subcategory: 'web-development', rating: 4.4, ratingCount: 1500, students: 7200, level: 'all-levels', duration: '32h', price: 39.99, originalPrice: 74.99, language: 'en', badge: null, thumbnail: 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&h=340&fit=crop', slug: 'uiux-masterclass' },
            { id: 7, title: 'AWS Cloud Architecture', instructor: 'James Kim', category: 'programming', subcategory: 'cloud', rating: 4.3, ratingCount: 1200, students: 4800, level: 'intermediate', duration: '36h', price: 49.99, originalPrice: 79.99, language: 'en', badge: null, thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=340&fit=crop', slug: 'aws-cloud' },
            { id: 8, title: 'Digital Marketing Strategy', instructor: 'Emma Wilson', category: 'marketing', subcategory: 'web-development', rating: 4.6, ratingCount: 980, students: 6200, level: 'beginner', duration: '24h', price: 34.99, originalPrice: 59.99, language: 'en', badge: null, thumbnail: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=340&fit=crop', slug: 'digital-marketing' },
            { id: 9, title: 'React Native Mobile Development', instructor: 'Carlos Mendez', category: 'programming', subcategory: 'web-development', rating: 4.8, ratingCount: 760, students: 3400, level: 'intermediate', duration: '40h', price: 64.99, originalPrice: 94.99, language: 'en', badge: 'new', thumbnail: 'https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&h=340&fit=crop', slug: 'react-native' },
            { id: 10, title: 'Photography Masterclass', instructor: 'Lisa Wang', category: 'photography', subcategory: 'python', rating: 4.9, ratingCount: 2200, students: 9500, level: 'all-levels', duration: '18h', price: 29.99, originalPrice: 49.99, language: 'en', badge: 'bestseller', thumbnail: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&h=340&fit=crop', slug: 'photography' },
            { id: 11, title: 'Calculus for Engineers', instructor: 'David Park', category: 'mathematics', subcategory: 'python', rating: 4.5, ratingCount: 540, students: 2800, level: 'advanced', duration: '30h', price: 0, originalPrice: null, language: 'en', badge: null, thumbnail: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=600&h=340&fit=crop', slug: 'calculus' },
            { id: 12, title: 'Spanish for Beginners', instructor: 'Maria Garcia', category: 'languages', subcategory: 'python', rating: 4.7, ratingCount: 1600, students: 11000, level: 'beginner', duration: '20h', price: 24.99, originalPrice: 44.99, language: 'es', badge: null, thumbnail: 'https://images.unsplash.com/photo-1508615070457-7e9eead1d6c7?w=600&h=340&fit=crop', slug: 'spanish-beginners' }
        ];
    }

    clearAllFilters() {
        // Use FiltersLoader's clear method instead
        if (filtersLoader) {
            filtersLoader.clearAllFilters();
        }
        this.activeFilters = { category: [], rating: [], level: [], price: [], duration: [], language: [], subcategory: [] };
        this.currentPage = 1;
        this.fetchCourses();
    }

    renderAll() {
        this.renderResultsInfo();
        this.renderActiveFilters();
        this.renderCourseGrid();
        this.renderPagination();
        this.checkEmpty();
    }

    renderResultsInfo() {
        const titleEl = document.getElementById('catalogTitle');
        const countEl = document.getElementById('resultsCount');

        if (titleEl) {
            // UPDATED: Show active category from filters if selected
            const activeCategories = this.activeFilters.category;
            if (activeCategories.length === 1) {
                const categoryNames = {
                    programming: 'Programming', 'data-science': 'Data Science',
                    business: 'Business', design: 'Design', engineering: 'Engineering',
                    mathematics: 'Mathematics', languages: 'Languages', marketing: 'Marketing',
                    photography: 'Photography', music: 'Music'
                };
                titleEl.textContent = categoryNames[activeCategories[0]] || 'All Courses';
            } else if (activeCategories.length > 1) {
                titleEl.textContent = 'Selected Categories';
            } else {
                titleEl.textContent = 'All Courses';
            }
        }
        if (countEl) {
            countEl.textContent = this.totalResults + ' result' + (this.totalResults !== 1 ? 's' : '');
        }
    }

    renderActiveFilters() {
        const container = document.getElementById('activeFiltersBar');
        const allFilters = [];
        const filterLabels = {
            category: 'Category',
            rating: 'Rating',
            level: 'Level',
            price: 'Price',
            duration: 'Duration',
            language: 'Language',
            subcategory: 'Subcategory'
        };

        Object.keys(this.activeFilters).forEach(key => {
            this.activeFilters[key].forEach(val => {
                // Skip "all-" prefixed values in display
                const displayVal = val.startsWith('all-') ? val.replace('all-', 'All ') : val;
                allFilters.push({ type: key, label: filterLabels[key] || key, value: displayVal, actualValue: val });
            });
        });

        if (allFilters.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = allFilters.map(f =>
            '<span class="filter-chip">' +
            f.label + ': ' + f.value +
            '<button class="filter-chip-remove" data-type="' + f.type + '" data-value="' + f.actualValue + '">' +
            '<i class="fas fa-times"></i></button></span>'
        ).join('') + '<button class="clear-all-link" id="clearAllLink">Clear all</button>';

        container.querySelectorAll('.filter-chip-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                const value = btn.dataset.value;
                this.activeFilters[type] = this.activeFilters[type].filter(v => v !== value);
                const cb = document.querySelector('.filter-input[data-filter="' + type + '"][value="' + value + '"]');
                if (cb) cb.checked = false;
                this.currentPage = 1;
                this.fetchCourses();
            });
        });

        const clearLink = document.getElementById('clearAllLink');
        if (clearLink) clearLink.addEventListener('click', () => this.clearAllFilters());
    }

    renderCourseGrid() {
        const container = document.getElementById('courseGrid');
        container.innerHTML = this.currentCourses.map(c => this.createCourseCard(c)).join('');

        container.querySelectorAll('.course-card-catalog').forEach(card => {
            card.addEventListener('click', () => {
                window.location.href = '/course/' + card.dataset.slug;
            });
        });
    }

    createCourseCard(course) {
        const levelClass = course.level === 'all-levels' ? 'all-levels' : course.level;
        const levelLabel = course.level === 'all-levels' ? 'All Levels' : this.capitalize(course.level);

        let badgeHTML = '';
        if (course.badge) {
            const badgeText = this.capitalize(course.badge);
            badgeHTML = `<span class="course-card-badge ${course.badge}">${badgeText}</span>`;
        }

        let priceHTML = '';
        if (course.price === 0) {
            priceHTML = '<span class="course-card-price-tag free">Free</span>';
        } else if (course.price) {
            priceHTML = `<span class="course-card-price-tag">$${course.price.toFixed(2)}</span>`;
        }

        let imageHTML = '';
        if (course.thumbnail) {
            imageHTML = `<img src="${course.thumbnail}" alt="${this.escapeHtml(course.title)}" loading="lazy">`;
        }

        return `
            <div class="course-card-catalog" data-slug="${course.slug}">
                <div class="course-card-thumb">
                    ${imageHTML}
                    ${badgeHTML}
                    ${priceHTML}
                </div>
                <div class="course-card-body">
                    <h3 class="course-card-title">${this.escapeHtml(course.title)}</h3>
                    <p class="course-card-instructor">${this.escapeHtml(course.instructor)}</p>
                    <div class="course-card-meta">
                        <span class="course-card-rating">
                            <i class="fas fa-star"></i> ${course.rating}
                            <span>(${this.formatNumber(course.ratingCount)})</span>
                        </span>
                        <span class="course-card-level ${levelClass}">${levelLabel}</span>
                    </div>
                    <div class="course-card-footer">
                        <span class="course-card-students">
                            <i class="fas fa-users"></i> ${this.formatNumber(course.students)}
                        </span>
                        <span class="course-card-duration">
                            <i class="fas fa-clock"></i> ${course.duration}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination() {
        const pageNumbers = document.getElementById('pageNumbers');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (this.totalPages <= 1) {
            if (pageNumbers) pageNumbers.innerHTML = '';
            if (prevBtn) prevBtn.disabled = true;
            if (nextBtn) nextBtn.disabled = true;
            return;
        }

        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= this.totalPages;

        if (pageNumbers) {
            let html = '';
            for (let i = 1; i <= this.totalPages; i++) {
                html += '<button class="page-number' + (i === this.currentPage ? ' active' : '') + '" data-page="' + i + '">' + i + '</button>';
            }
            pageNumbers.innerHTML = html;

            pageNumbers.querySelectorAll('.page-number').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.currentPage = parseInt(btn.dataset.page);
                    this.fetchCourses();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
            });
        }
    }

    changePage(delta) {
        const newPage = this.currentPage + delta;
        if (newPage >= 1 && newPage <= this.totalPages) {
            this.currentPage = newPage;
            this.fetchCourses();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    checkEmpty() {
        const grid = document.getElementById('courseGrid');
        const empty = document.getElementById('emptyCatalog');
        const pagination = document.getElementById('pagination');

        if (this.totalResults === 0) {
            if (grid) grid.style.display = 'none';
            if (pagination) pagination.style.display = 'none';
            if (empty) empty.style.display = '';
        } else {
            if (grid) grid.style.display = '';
            if (pagination) pagination.style.display = '';
            if (empty) empty.style.display = 'none';
        }
    }

// Replace these methods in your CourseCatalogPage class:

showLoading() {
    // Create overlay
    let overlay = document.getElementById('catalogLoadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'catalogLoadingOverlay';
        overlay.className = 'catalog-loading-overlay';
        overlay.innerHTML = `
            <div class="catalog-loader">
                <div class="loader-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <div class="loader-text">
                    <span class="loader-dot">.</span>
                    <span class="loader-dot">.</span>
                    <span class="loader-dot">.</span>
                </div>
            </div>
        `;
        document.querySelector('.catalog-main').appendChild(overlay);
    }

    overlay.classList.add('active');

    // Show skeleton placeholders in grid for better UX
    const grid = document.getElementById('courseGrid');
    if (grid && this.currentCourses.length === 0) {
        // Only show skeletons on first load
        let skeletonHTML = '';
        for (let i = 0; i < 6; i++) {
            skeletonHTML += `
                <div class="course-card-skeleton">
                    <div class="skeleton-thumb"></div>
                    <div class="skeleton-body">
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line short"></div>
                        <div class="skeleton-line medium"></div>
                    </div>
                </div>
            `;
        }
        grid.innerHTML = skeletonHTML;
    } else if (grid) {
        grid.classList.add('loading-blur');
    }
}
hideLoading() {
    const overlay = document.getElementById('catalogLoadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }

    const grid = document.getElementById('courseGrid');
    if (grid) {
        grid.classList.remove('loading-blur');
    }
}

    showError(message) {
        const grid = document.getElementById('courseGrid');
        if (grid) {
            grid.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> ' + this.escapeHtml(message) + '</div>';
        }
    }

    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toString();
    }

    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    escapeHtml(text) {
        if (!text) return '';
        return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
}

// ============================================
// BOOTSTRAP
// ============================================
let catalogPage;
document.addEventListener('DOMContentLoaded', function() {
    catalogPage = new CourseCatalogPage();
});
