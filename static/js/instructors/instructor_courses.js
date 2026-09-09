// ============================================
// INSTRUCTOR MY COURSES PAGE CONTROLLER
// ============================================

class InstructorCoursesPage {
    constructor() {
        this.activeTab = 'all';
        this.searchQuery = '';
        this.activeFilters = { category: [], version: [] };
        this.sortBy = 'updated-desc';
        this.currentPage = 1;
        this.perPage = 6;
        this.allCourses = [];
        this.filteredCourses = [];
        this.selectedCourses = new Set();
        this.openActionMenu = null;
        this.pendingConfirm = null;
        this.pendingPublishCourse = null;
        this.availableCategories = [];
        this.availableVersions = [];
        this.init();
    }

    async init() {
        this.ensurePublishModalExists();
        this.bindEvents();
        await this.loadCourses();
        this.hideLoader();
    }

    ensurePublishModalExists() {
        if (document.getElementById('publishOverlay')) return;

        const modalHtml = `
            <div id="publishOverlay" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center;">
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 450px; width: 90%; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3 id="publishTitle" style="margin: 0; font-size: 20px; font-weight: 600; color: #333;">Publish Course</h3>
                        <button id="publishClose" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                    </div>
                    <p id="publishMessage" style="margin: 0 0 15px 0; color: #666; line-height: 1.5;">Your course has been approved and is ready to be published. Once published, it will be visible to all students.</p>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <strong id="publishCourseName" style="color: #333; font-size: 16px;"></strong>
                    </div>
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button id="publishCancel" style="padding: 10px 20px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; color: #666;">Cancel</button>
                        <button id="publishConfirm" style="padding: 10px 20px; border: none; background: #4F46E5; color: white; border-radius: 6px; cursor: pointer; font-weight: 500;">
                            <i class="fas fa-check-circle"></i> Publish Course
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    bindEvents() {
        document.querySelectorAll('.course-tab').forEach(tab => tab.addEventListener('click', () => this.switchTab(tab.dataset.tab)));

        const searchInput = document.getElementById('courseSearch');
        const searchClear = document.getElementById('searchClearBtn');
        searchInput?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase().trim();
            searchClear.style.display = this.searchQuery ? 'flex' : 'none';
            this.applyFilters();
        });
        searchClear?.addEventListener('click', () => {
            searchInput.value = '';
            this.searchQuery = '';
            searchClear.style.display = 'none';
            this.applyFilters();
        });

        document.getElementById('sortSelect')?.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.applyFilters();
        });

        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const menuId = btn.dataset.filter === 'category' ? 'filterCategory' : 'filterVersion';
                const menu = document.getElementById(menuId);
                document.querySelectorAll('.filter-menu.open').forEach(m => { if (m !== menu) m.classList.remove('open'); });
                menu?.classList.toggle('open');
            });
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-dropdown')) document.querySelectorAll('.filter-menu.open').forEach(m => m.classList.remove('open'));
        });

        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));

        document.addEventListener('click', (e) => {
            if (this.openActionMenu && !e.target.closest('.card-more-btn') && !e.target.closest('.course-actions-menu')) this.closeActionMenu();
        });

        document.getElementById('confirmCancel')?.addEventListener('click', () => this.closeConfirm());
        document.getElementById('confirmOk')?.addEventListener('click', () => this.executeConfirm());

        // Use event delegation for publish modal (works with dynamically created elements)
        document.addEventListener('click', (e) => {
            if (e.target.id === 'publishCancel' || e.target.closest('#publishCancel')) {
                this.closePublishModal();
            }
            if (e.target.id === 'publishConfirm' || e.target.closest('#publishConfirm')) {
                this.executePublish();
            }
            if (e.target.id === 'publishClose' || e.target.closest('#publishClose')) {
                this.closePublishModal();
            }
            if (e.target.id === 'publishOverlay') {
                this.closePublishModal();
            }
        });

        document.getElementById('prevPage')?.addEventListener('click', () => this.changePage(-1));
        document.getElementById('nextPage')?.addEventListener('click', () => this.changePage(1));
    }

    collectFilters() {
        this.activeFilters = { category: [], version: [] };
        document.querySelectorAll('#filterCategory input:checked').forEach(cb => this.activeFilters.category.push(cb.value));
        document.querySelectorAll('#filterVersion input:checked').forEach(cb => this.activeFilters.version.push(cb.value));
    }

    mapData(allCourse) {
        const payloads = [];
        allCourse.forEach(course => {
            const { last_updated, review_status, ...rest } = course;
            const payload = {
                ...rest,
                lastUpdated: new Date(last_updated),
                reviewStatus: review_status,
            };
            payloads.push(payload);
        });
        return payloads;
    }

    extractFilterOptions(courses) {
        const categories = new Set();
        const versions = new Set();

        courses.forEach(course => {
            if (course.category) {
                categories.add(course.category);
            }
            if (course.version) {
                versions.add(course.version);
            }
        });

        this.availableCategories = Array.from(categories).sort();
        this.availableVersions = Array.from(versions).sort((a, b) => {
            const aParts = a.split('.').map(Number);
            const bParts = b.split('.').map(Number);
            for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
                const aVal = aParts[i] || 0;
                const bVal = bParts[i] || 0;
                if (aVal !== bVal) return bVal - aVal;
            }
            return 0;
        });
    }

    populateFilterDropdowns() {
        const categoryContainer = document.getElementById('filterCategory');
        const versionContainer = document.getElementById('filterVersion');

        if (categoryContainer) {
            categoryContainer.innerHTML = this.availableCategories.map(category => `
                <label class="filter-option">
                    <input type="checkbox" value="${category}">
                    <span>${this.capitalize(category)}</span>
                </label>
            `).join('');

            categoryContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                cb.addEventListener('change', () => {
                    this.collectFilters();
                    this.applyFilters();
                });
            });
        }

        if (versionContainer) {
            versionContainer.innerHTML = this.availableVersions.map(version => `
                <label class="filter-option">
                    <input type="checkbox" value="${version}">
                    <span>v${version}</span>
                </label>
            `).join('');

            versionContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                cb.addEventListener('change', () => {
                    this.collectFilters();
                    this.applyFilters();
                });
            });
        }
    }

    updateFilterCounts() {
        const categoryCount = this.activeFilters.category.length;
        const versionCount = this.activeFilters.version.length;

        const categoryBtn = document.querySelector('.filter-btn[data-filter="category"]');
        const versionBtn = document.querySelector('.filter-btn[data-filter="version"]');

        if (categoryBtn) {
            const countBadge = categoryBtn.querySelector('.filter-count') || document.createElement('span');
            countBadge.className = 'filter-count';
            if (categoryCount > 0) {
                countBadge.textContent = categoryCount;
                if (!categoryBtn.contains(countBadge)) {
                    categoryBtn.appendChild(countBadge);
                }
            } else {
                countBadge.remove();
            }
        }

        if (versionBtn) {
            const countBadge = versionBtn.querySelector('.filter-count') || document.createElement('span');
            countBadge.className = 'filter-count';
            if (versionCount > 0) {
                countBadge.textContent = versionCount;
                if (!versionBtn.contains(countBadge)) {
                    versionBtn.appendChild(countBadge);
                }
            } else {
                countBadge.remove();
            }
        }
    }

    async loadCourses() {
        this.showSkeletons();

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/courses/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load Courses.");
            }

            const data = await response.json();
            this.allCourses = this.mapData(data.results ?? []);
            console.log(this.allCourses);

            // Extract unique categories and versions from the loaded courses
            this.extractFilterOptions(this.allCourses);
            // Populate filter dropdowns dynamically
            this.populateFilterDropdowns();

        } catch (error) {
            console.error("Error loading categories:", error);
            // Fallback to dummy data if API fails
            this.allCourses = this.getDummyCourses();
            this.extractFilterOptions(this.allCourses);
            this.populateFilterDropdowns();
        }

        this.applyFilters();
    }

    getDummyCourses() {
        return [
            {
                id: 1,
                title: 'Python for Data Science',
                category: 'data-science',
                status: 'published',
                version: '2.1',
                rating: 4.8,
                students: 1245,
                revenue: 24000,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 2 * 86400000),
                slug: 'python-data-science'
            },
            {
                id: 2,
                title: 'Machine Learning A-Z',
                category: 'machine-learning',
                status: 'published',
                version: '1.5',
                rating: 4.6,
                students: 890,
                revenue: 18000,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 7 * 86400000),
                slug: 'ml-az'
            },
            {
                id: 3,
                title: 'Deep Learning Specialization',
                category: 'machine-learning',
                status: 'published',
                version: '3.0',
                rating: 4.9,
                students: 640,
                revenue: 14000,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 3 * 86400000),
                slug: 'deep-learning'
            },
            {
                id: 4,
                title: 'Data Engineering Essentials',
                category: 'data-science',
                status: 'published',
                version: '1.2',
                rating: 4.5,
                students: 520,
                revenue: 10500,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 5 * 86400000),
                slug: 'data-engineering'
            },
            {
                id: 5,
                title: 'SQL for Data Analysis',
                category: 'data-science',
                status: 'published',
                version: '2.0',
                rating: 4.7,
                students: 780,
                revenue: 15600,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 10 * 86400000),
                slug: 'sql-analysis'
            },
            {
                id: 6,
                title: 'Cloud Computing with AWS',
                category: 'cloud',
                status: 'published',
                version: '1.0',
                rating: 4.4,
                students: 430,
                revenue: 8600,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 14 * 86400000),
                slug: 'aws-cloud'
            },
            {
                id: 7,
                title: 'Full-Stack Web Development',
                category: 'web-development',
                status: 'published',
                version: '1.8',
                rating: 4.3,
                students: 380,
                revenue: 7600,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 21 * 86400000),
                slug: 'fullstack-web'
            },
            {
                id: 8,
                title: 'Advanced ML Techniques',
                category: 'machine-learning',
                status: 'updated',
                version: '2.0',
                rating: 4.2,
                students: 210,
                revenue: 4200,
                reviewStatus: 'pending',
                thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 1 * 86400000),
                slug: 'advanced-ml'
            },
            {
                id: 9,
                title: 'Advanced NLP with Transformers',
                category: 'machine-learning',
                status: 'draft',
                version: '0.1',
                progress: 60,
                reviewStatus: 'not_submitted',
                thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 1 * 86400000),
                slug: 'advanced-nlp'
            },
            {
                id: 10,
                title: 'Computer Vision 2026',
                category: 'machine-learning',
                status: 'draft',
                version: '0.1',
                progress: 35,
                reviewStatus: 'not_submitted',
                thumbnail: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 4 * 86400000),
                slug: 'cv-2026'
            },
            {
                id: 11,
                title: 'Reinforcement Learning',
                category: 'machine-learning',
                status: 'draft',
                version: '0.1',
                progress: 10,
                reviewStatus: 'not_submitted',
                thumbnail: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 8 * 86400000),
                slug: 'rl-course'
            },
            {
                id: 12,
                title: 'SQL for Data Analysis v2',
                category: 'data-science',
                status: 'submitted',
                version: '2.5',
                progress: 95,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 1 * 86400000),
                slug: 'sql-v2'
            },
            {
                id: 13,
                title: 'Python for DS Update',
                category: 'data-science',
                status: 'under_review',
                version: '3.0',
                progress: 100,
                reviewStatus: 'pending',
                thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 3 * 86400000),
                slug: 'python-ds-update'
            },
            {
                id: 14,
                title: 'ML A-Z Refresh',
                category: 'machine-learning',
                status: 'under_review',
                version: '2.0',
                progress: 100,
                reviewStatus: 'pending',
                thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 5 * 86400000),
                slug: 'ml-az-refresh'
            },
            {
                id: 15,
                title: 'Intro to Statistics',
                category: 'data-science',
                status: 'archived',
                version: '1.0',
                rating: 4.0,
                students: 150,
                revenue: 3000,
                reviewStatus: 'approved',
                thumbnail: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=340&fit=crop',
                lastUpdated: new Date(Date.now() - 90 * 86400000),
                slug: 'intro-stats'
            }
        ];
    }

    applyFilters() {
        let courses = [...this.allCourses];
        if (this.activeTab !== 'all') courses = courses.filter(c => c.status === this.activeTab);
        if (this.searchQuery) courses = courses.filter(c => c.title.toLowerCase().includes(this.searchQuery) || c.category.toLowerCase().includes(this.searchQuery));
        if (this.activeFilters.category.length > 0) courses = courses.filter(c => this.activeFilters.category.includes(c.category));
        if (this.activeFilters.version.length > 0) courses = courses.filter(c => this.activeFilters.version.includes(c.version));
        courses = this.sortCourses(courses);
        this.filteredCourses = courses;
        this.selectedCourses.clear();
        this.currentPage = 1;
        this.renderAll();
    }

    sortCourses(courses) {
        switch (this.sortBy) {
            case 'updated-desc': return courses.sort((a, b) => b.lastUpdated - a.lastUpdated);
            case 'updated-asc': return courses.sort((a, b) => a.lastUpdated - b.lastUpdated);
            case 'students-desc': return courses.sort((a, b) => (b.students || 0) - (a.students || 0));
            case 'rating-desc': return courses.sort((a, b) => (b.rating || 0) - (a.rating || 0));
            case 'revenue-desc': return courses.sort((a, b) => (b.revenue || 0) - (a.revenue || 0));
            case 'alpha-asc': return courses.sort((a, b) => a.title.localeCompare(b.title));
            default: return courses;
        }
    }

    switchTab(tab) {
        this.activeTab = tab;
        document.querySelectorAll('.course-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`.course-tab[data-tab="${tab}"]`)?.classList.add('active');
        this.applyFilters();
    }

    renderAll() {
        this.updateTabCounts();
        this.renderActiveFilterChips();
        this.renderResultsInfo();
        this.renderCourseGrid();
        this.renderPagination();
        this.checkEmptyState();
        this.updateFilterCounts();
    }

    updateTabCounts() {
        const count = (status) => this.allCourses.filter(c => c.status === status).length;
        document.getElementById('countAll').textContent = this.allCourses.length;
        document.getElementById('countDraft').textContent = count('draft');
        document.getElementById('countReadyForReview').textContent = count('submitted');
        document.getElementById('countUnderReview').textContent = count('under_review');
        document.getElementById('countPublished').textContent = count('published');
        document.getElementById('countUpdated').textContent = count('updated');
        document.getElementById('countArchived').textContent = count('archived');
    }

    renderActiveFilterChips() {
        const container = document.getElementById('activeFilters');
        const filters = [
            ...this.activeFilters.category.map(v => ({ type: 'Category', value: v })),
            ...this.activeFilters.version.map(v => ({ type: 'Version', value: v }))
        ];
        if (filters.length === 0) { container.style.display = 'none'; return; }
        container.style.display = 'flex';
        container.innerHTML = filters.map(f => `
            <span class="filter-chip">${f.type}: ${this.capitalize(f.value)}<button class="filter-chip-remove" data-type="${f.type.toLowerCase()}" data-value="${f.value}"><i class="fas fa-times"></i></button></span>
        `).join('') + '<button class="clear-all-filters" id="clearAllFilters">Clear all</button>';
        container.querySelectorAll('.filter-chip-remove').forEach(btn => {
            btn.addEventListener('click', () => this.removeFilter(btn.dataset.type, btn.dataset.value));
        });
        document.getElementById('clearAllFilters')?.addEventListener('click', () => this.clearAllFilters());
    }

    removeFilter(type, value) {
        const map = { 'category': 'category', 'version': 'version' };
        const key = map[type];
        if (key) {
            this.activeFilters[key] = this.activeFilters[key].filter(v => v !== value);
            const menuId = key === 'category' ? 'filterCategory' : 'filterVersion';
            const cb = document.querySelector(`#${menuId} input[value="${value}"]`);
            if (cb) cb.checked = false;
            this.applyFilters();
        }
    }

    clearAllFilters() {
        this.activeFilters = { category: [], version: [] };
        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(cb => cb.checked = false);
        this.applyFilters();
    }

    renderResultsInfo() {
        document.getElementById('showingCount').textContent = this.filteredCourses.length;
    }

    renderCourseGrid() {
        const container = document.getElementById('coursesGrid');
        const start = (this.currentPage - 1) * this.perPage;
        const pageCourses = this.filteredCourses.slice(start, start + this.perPage);
        container.innerHTML = pageCourses.map(c => this.createCourseCard(c)).join('');
        this.bindCardEvents(container);
    }

    createCourseCard(course) {
        const isPublished = course.status === 'published';
        const isDraft = course.status === 'draft';
        const isSubmitted = course.status === 'submitted';
        const isUnderReview = course.status === 'under_review';
        const isUpdated = course.status === 'updated';
        const isArchived = course.status === 'archived';
        const showFullStats = isPublished || isUpdated || isArchived;
        const showDraftProgress = isDraft || isSubmitted || isUnderReview;

        const statusLabel = course.status.replace(/_/g, ' ');
        const reviewLabel = course.reviewStatus.replace(/_/g, ' ');

        let statsHtml = '';
        if (showFullStats) {
            statsHtml = `
                <div class="course-card-stats">
                    <span class="course-stat-item version"><i class="fas fa-code-branch"></i> v${course.version}</span>
                    ${course.rating ? `<span class="course-stat-item rating"><i class="fas fa-star"></i> ${course.rating}</span>` : ''}
                    ${course.students ? `<span class="course-stat-item"><i class="fas fa-users"></i> ${this.formatNum(course.students)}</span>` : ''}
                    ${course.revenue ? `<span class="course-stat-item">$${this.formatRevenue(course.revenue)}</span>` : ''}
                    <span class="course-stat-item status-indicator ${course.status}"><i class="fas fa-circle"></i> ${this.capitalize(statusLabel)}</span>
                </div>
            `;
        } else if (showDraftProgress) {
            statsHtml = `
                <div class="course-card-stats">
                    <span class="course-stat-item version"><i class="fas fa-code-branch"></i> v${course.version}</span>
                    <span class="course-stat-item status-indicator ${course.status}"><i class="fas fa-circle"></i> ${this.capitalize(statusLabel)}</span>
                </div>
                ${course.progress !== undefined ? `
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${course.progress}%"></div>
                </div>
                <span class="progress-text">${course.progress}% complete</span>
                ` : ''}
            `;
        }

        let footerHtml = '';
        if (isPublished) {
            footerHtml = `
                <span class="last-updated">Updated ${this.formatRelative(course.lastUpdated)}</span>
                <button class="card-action-btn view" data-id="${course.id}" data-slug="${course.slug}"><i class="fas fa-eye"></i> View</button>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        } else if (isUpdated) {
            footerHtml = `
                <span class="last-updated">Updated ${this.formatRelative(course.lastUpdated)}</span>
                <button class="card-action-btn view" data-id="${course.id}" data-slug="${course.slug}"><i class="fas fa-eye"></i> View</button>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        } else if (isDraft) {
            footerHtml = `
                <span class="last-updated">Last edited ${this.formatRelative(course.lastUpdated)}</span>
                <button class="card-action-btn edit" data-id="${course.id}" data-slug="${course.slug}"><i class="fas fa-pen"></i> Edit</button>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        } else if (isSubmitted) {
            footerHtml = `
                <span class="last-updated">Submitted ${this.formatRelative(course.lastUpdated)}</span>
                <button class="card-action-btn preview" data-id="${course.id}" data-slug="${course.slug}"><i class="fas fa-eye"></i> Preview</button>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        } else if (isUnderReview) {
            footerHtml = `
                <span class="last-updated">In review</span>
                <button class="card-action-btn preview" data-id="${course.id}" data-slug="${course.slug}"><i class="fas fa-eye"></i> Preview</button>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        } else if (isArchived) {
            footerHtml = `
                <span class="last-updated">Archived ${this.formatRelative(course.lastUpdated)}</span>
                <button class="card-more-btn" data-id="${course.id}"><i class="fas fa-ellipsis-h"></i></button>
            `;
        }

        return `
            <div class="course-card-instructor" data-id="${course.id}">
                <input type="checkbox" class="card-select-checkbox" data-id="${course.id}">
                <div class="course-card-thumb">
                    <img src="${course.thumbnail}" alt="${course.title}" onerror="this.src='https://via.placeholder.com/600x340/4F46E5/FFFFFF?text=Course'">
                    <span class="course-status-badge ${course.status}">${this.capitalize(statusLabel)}</span>
                    <span class="review-status-badge ${course.reviewStatus}">${this.capitalize(reviewLabel)}</span>
                    <span class="version-badge">v${course.version}</span>
                </div>
                <div class="course-card-body-instructor">
                    <h3 class="course-card-title-instructor">${course.title}</h3>
                    <span class="course-card-category">${this.capitalize(course.category)}</span>
                    ${statsHtml}
                    <div class="course-card-footer-instructor">${footerHtml}</div>
                </div>
            </div>
        `;
    }

    bindCardEvents(container) {
        container.querySelectorAll('.card-select-checkbox').forEach(cb => {
            cb.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(cb.dataset.id);
                cb.checked ? this.selectedCourses.add(id) : this.selectedCourses.delete(id);
                cb.closest('.course-card-instructor')?.classList.toggle('selected', cb.checked);
            });
        });

        container.querySelectorAll('.card-action-btn.view').forEach(b => {
            b.addEventListener('click', (e) => {
                e.stopPropagation();
                const slug = b.dataset.slug;
                const id = b.dataset.id;
                window.open(`/courses/${id}/${slug}`, '_blank');
            });
        });

        container.querySelectorAll('.card-action-btn.edit, .card-action-btn.draft-edit').forEach(b => {
            b.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = b.dataset.id;
                const slug = b.dataset.slug;
                window.location.href = `/instructor/courses/${slug}/${id}/edit`;
            });
        });

        container.querySelectorAll('.card-action-btn.preview').forEach(b => {
            b.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = b.dataset.id;
                window.open(`/instructor/courses/${id}/preview/`, '_blank');
            });
        });

        container.querySelectorAll('.card-more-btn').forEach(b => {
            b.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleActionMenu(parseInt(b.dataset.id), b);
            });
        });
    }

    toggleSelectAll(checked) {
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredCourses.slice(start, start + this.perPage);
        page.forEach(c => checked ? this.selectedCourses.add(c.id) : this.selectedCourses.delete(c.id));
        document.querySelectorAll('.card-select-checkbox').forEach(cb => {
            cb.checked = checked;
            cb.closest('.course-card-instructor')?.classList.toggle('selected', checked);
        });
    }

    toggleActionMenu(id, btn) {
        if (this.openActionMenu === id) { this.closeActionMenu(); return; }
        this.closeActionMenu();
        this.openActionMenu = id;
        const course = this.allCourses.find(c => c.id === id);
        if (!course) return;
        const rect = btn.getBoundingClientRect();
        const portal = document.getElementById('actionsDropdownPortal');
        const menu = document.getElementById('courseActionsMenu');

        let items = '';

        // Edit (all except archived)
        if (course.status !== 'archived') {
            items += `<button class="action-item" data-action="edit" data-id="${id}" data-slug="${course.slug}"><i class="fas fa-pen"></i> Edit Course</button>`;
        }

        // Preview (all)
        items += `<button class="action-item" data-action="preview" data-id="${id}" data-slug="${course.slug}"><i class="fas fa-eye"></i> Preview</button>`;

        // Publish (submitted with approved review status)
        if (course.status === 'submitted' && course.reviewStatus === 'approved') {
            items += `<button class="action-item publish-action" data-action="publish" data-id="${id}"><i class="fas fa-check-circle"></i> Publish</button>`;
        }

        // Submit for Review (draft)
        if (course.status === 'draft' && course.reviewStatus === 'not_submitted') {
            items += `<button class="action-item" data-action="submit-review" data-id="${id}"><i class="fas fa-paper-plane"></i> Submit for Review</button>`;
        }

        // Delete (draft only)
        if (course.status === 'draft') {
            items += `<button class="action-item danger" data-action="delete" data-id="${id}"><i class="fas fa-trash-alt"></i> Delete Draft</button>`;
        }

        menu.innerHTML = items;
        portal.style.display = 'block';
        portal.style.top = Math.min(rect.bottom + 4, window.innerHeight - 300) + 'px';
        portal.style.left = Math.min(rect.right - 200, window.innerWidth - 210) + 'px';

        menu.querySelectorAll('.action-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                const courseId = parseInt(item.dataset.id);
                this.closeActionMenu();
                this.handleCourseAction(action, courseId);
            });
        });
    }

    closeActionMenu() {
        this.openActionMenu = null;
        const portal = document.getElementById('actionsDropdownPortal');
        if (portal) portal.style.display = 'none';
    }

    handleCourseAction(action, id) {
        const course = this.allCourses.find(c => c.id === id);
        if (!course) return;

        switch (action) {
            case 'edit':
                window.location.href = `/instructor/courses/${course.slug}/${id}/edit`;
                break;
            case 'preview':
                window.open(`/instructor/courses/${course.id}/preview/`, '_blank');
                break;
            case 'duplicate':
                this.allCourses.push({
                    ...course,
                    id: Date.now(),
                    title: course.title + ' (Copy)',
                    status: 'draft',
                    version: '0.1',
                    progress: 0,
                    students: 0,
                    revenue: 0,
                    reviewStatus: 'not_submitted',
                    slug: course.slug + '-copy'
                });
                this.applyFilters();
                this.showToast('Course duplicated');
                break;
            case 'publish':
                this.showPublishModal(course);
                break;
            case 'submit-review':
                this.showConfirm(
                    `Submit "${course.title}" for Review?`,
                    'This course will be submitted for review and cannot be edited until the review is complete.',
                    () => {
                        this.submitCourse(id);
                    }
                );
                break;
            case 'archive':
                course.status = 'archived';
                this.applyFilters();
                this.showToast(`"${course.title}" archived`);
                break;
            case 'restore':
                course.status = 'draft';
                course.reviewStatus = 'not_submitted';
                this.applyFilters();
                this.showToast(`"${course.title}" restored to drafts`);
                break;
            case 'analytics':
                window.location.href = `/instructor/analytics?course=${course.slug}`;
                break;
            case 'delete':
                this.showConfirm(
                    `Delete "${course.title}"?`,
                    'This cannot be undone.',
                    () => {
                        this.deleteCourse(id);
                    }
                );
                break;
        }
    }

    showPublishModal(course) {
        this.pendingPublishCourse = course;

        // Update modal content
        const publishTitle = document.getElementById('publishTitle');
        const publishMessage = document.getElementById('publishMessage');
        const publishCourseName = document.getElementById('publishCourseName');

        if (publishTitle) publishTitle.textContent = 'Publish Course';
        if (publishMessage) publishMessage.textContent = 'Your course has been approved and is ready to be published. Once published, it will be visible to all students.';
        if (publishCourseName) publishCourseName.textContent = course.title;

        // Show modal
        const overlay = document.getElementById('publishOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
            overlay.style.zIndex = '9999';
        } else {
            console.error('Publish overlay not found');
            this.showToast('Error: Publish modal not found');
        }
    }

    closePublishModal() {
        const overlay = document.getElementById('publishOverlay');
        if (overlay) overlay.style.display = 'none';
        this.pendingPublishCourse = null;
    }

    async executePublish() {
        if (!this.pendingPublishCourse) return;

        const course = this.pendingPublishCourse;
        const publishBtn = document.getElementById('publishConfirm');

        // Disable button and show loading state
        if (publishBtn) {
            publishBtn.disabled = true;
            publishBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publishing...';
        }

        try {
            await this.publishCourse(course.id);
            this.closePublishModal();
        } catch (error) {
            console.error('Error publishing course:', error);
            this.showToast('Failed to publish course. Please try again.');
        } finally {
            // Re-enable button
            if (publishBtn) {
                publishBtn.disabled = false;
                publishBtn.innerHTML = '<i class="fas fa-check-circle"></i> Publish Course';
            }
        }
    }

    async publishCourse(courseId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/courses/${courseId}/publish/`,
                {
                    method: "POST",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to publish course.");
            }

            const data = await response.json();

            // Update the course in the local array
            const course = this.allCourses.find(c => c.id === courseId);
            if (course) {
                course.status = 'published';
                course.reviewStatus = 'approved';
            }

            this.applyFilters();
            this.showToast('Course published successfully!');

            return data;
        } catch (error) {
            console.error("Error publishing course:", error);
            this.showToast('Failed to publish course. Please try again.');
            throw error;
        }
    }

    async submitCourse(courseId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/courses/${courseId}/submit/`,
                {
                    method: "POST",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to submit course for review.");
            }

            const data = await response.json();

            // Update the course in the local array
            const course = this.allCourses.find(c => c.id === courseId);
            if (course) {
                course.status = 'submitted';
                course.reviewStatus = 'pending';
            }

            this.applyFilters();
            this.showToast('Course submitted for review successfully!');

            return data;
        } catch (error) {
            console.error("Error submitting course for review:", error);
            this.showToast('Failed to submit course for review. Please try again.');
            throw error;
        }
    }

    async deleteCourse(courseId) {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/courses/${courseId}/delete/`,
                {
                    method: "DELETE",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to delete course.");
            }

            this.allCourses = this.allCourses.filter(c => c.id !== courseId);
            this.showToast('Draft deleted');
        } catch (error) {
            console.error("Error deleting course, try later:", error);
            this.showToast('Failed to delete course. Please try again.');
        }

        this.applyFilters();
    }

    showConfirm(title, message, cb) {
        document.getElementById('confirmTitle').textContent = title;
        document.getElementById('confirmMessage').textContent = message;
        document.getElementById('confirmOverlay').style.display = 'flex';
        this.pendingConfirm = cb;
    }

    closeConfirm() {
        document.getElementById('confirmOverlay').style.display = 'none';
        this.pendingConfirm = null;
    }

    executeConfirm() {
        if (this.pendingConfirm) this.pendingConfirm();
        this.closeConfirm();
    }

    renderPagination() {
        const total = Math.ceil(this.filteredCourses.length / this.perPage);
        const c = document.getElementById('pageNumbers');
        if (total <= 1) {
            c.innerHTML = '';
            document.getElementById('prevPage').disabled = true;
            document.getElementById('nextPage').disabled = true;
            return;
        }
        document.getElementById('prevPage').disabled = this.currentPage <= 1;
        document.getElementById('nextPage').disabled = this.currentPage >= total;
        c.innerHTML = Array.from({ length: total }, (_, i) => `<button class="page-number ${i + 1 === this.currentPage ? 'active' : ''}" data-page="${i + 1}">${i + 1}</button>`).join('');
        c.querySelectorAll('.page-number').forEach(b => b.addEventListener('click', () => {
            this.currentPage = parseInt(b.dataset.page);
            this.renderCourseGrid();
            this.renderPagination();
        }));
    }

    changePage(d) {
        const total = Math.ceil(this.filteredCourses.length / this.perPage);
        const np = this.currentPage + d;
        if (np >= 1 && np <= total) {
            this.currentPage = np;
            this.renderCourseGrid();
            this.renderPagination();
        }
    }

    checkEmptyState() {
        const grid = document.getElementById('coursesGrid');
        const empty = document.getElementById('emptyState');
        const pag = document.getElementById('pagination');
        if (this.filteredCourses.length === 0) {
            grid.style.display = 'none';
            pag.style.display = 'none';
            empty.style.display = 'block';
            const msgs = {
                all: { icon: '📚', title: 'No courses yet', desc: 'Start creating your first course!', btn: true },
                draft: { icon: '📝', title: 'No draft courses', desc: 'Start creating a new course.', btn: true },
                submitted: { icon: '📋', title: 'No submitted courses', desc: 'Complete a draft to submit it for review.', btn: false },
                under_review: { icon: '🔍', title: 'No courses under review', desc: 'Submitted courses will appear here.', btn: false },
                published: { icon: '✅', title: 'No published courses', desc: 'Publish a course to see it here.', btn: false },
                updated: { icon: '🔄', title: 'No updated courses', desc: 'Updated courses will appear here.', btn: false },
                archived: { icon: '📦', title: 'No archived courses', desc: 'Archive courses you no longer want active.', btn: false }
            };
            const m = msgs[this.activeTab] || msgs.all;
            empty.innerHTML = `<span class="empty-courses-icon">${m.icon}</span><h3>${m.title}</h3><p>${m.desc}</p>${m.btn ? '<button class="empty-create-btn" onclick="window.location.href=\'/instructor/courses/create\'"><i class="fas fa-plus"></i> Create Course</button>' : ''}`;
        } else {
            grid.style.display = '';
            pag.style.display = '';
            empty.style.display = 'none';
        }
    }

    showSkeletons() {
        document.getElementById('coursesGrid').innerHTML = Array(6).fill('<div class="course-card-skeleton"><div class="skeleton-block" style="height:180px;"></div><div style="padding:16px;"><div class="skeleton-line"></div><div class="skeleton-line" style="width:50%;"></div></div></div>').join('');
    }

    hideLoader() {
        const loader = document.getElementById('loadingOverlay');
        if (loader) loader.classList.add('hidden');
    }

    capitalize(str) {
        if (!str) return '';
        return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    formatNum(n) {
        if (!n) return '0';
        return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : n.toString();
    }

    formatRevenue(n) {
        if (!n) return '0';
        return n >= 1000 ? (n / 1000).toFixed(1) + 'K' : n.toString();
    }

    formatRelative(d) {
        const diff = Math.floor((Date.now() - d) / 86400000);
        if (diff === 0) return 'today';
        if (diff === 1) return 'yesterday';
        if (diff < 7) return diff + 'd ago';
        if (diff < 30) return Math.floor(diff / 7) + 'w ago';
        return Math.floor(diff / 30) + 'mo ago';
    }

    showToast(m) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(toastContainer);
        }

        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = m;
        t.style.cssText = `
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            max-width: 300px;
        `;
        toastContainer.appendChild(t);
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
}

let instructorCoursesPage;
document.addEventListener('DOMContentLoaded', () => {
    instructorCoursesPage = new InstructorCoursesPage();
});
