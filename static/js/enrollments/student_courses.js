// ============================================
// MY LEARNING PAGE CONTROLLER
// ============================================

class MyLearningPage {
    constructor() {
        this.activeTab = 'all';
        this.searchQuery = '';
        this.activeFilters = { status: [], difficulty: [], category: [] };
        this.sortBy = 'recent';
        this.currentPage = 1;
        this.perPage = 6;
        this.allCourses = [];
        this.filteredCourses = [];
        this.openActionMenu = null;
        this.isLoading = false;

        this.init();
    }

    async init() {
        console.log('MyLearningPage initializing...');
        this.bindEvents();

        try {
            await this.loadCourses();
        } catch (error) {
            console.error('Error during initialization:', error);
            this.allCourses = this.getDummyCourses();
            this.applyFilters();
        } finally {
            this.forceHideLoader();
        }
    }

    bindEvents() {


        // Tab clicks
        document.querySelectorAll('.learning-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });

        // Search input
        const searchInput = document.getElementById('learningSearch');
        const searchClear = document.getElementById('searchClearBtn');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase().trim();
                if (searchClear) {
                    searchClear.style.display = this.searchQuery ? 'flex' : 'none';
                }
                this.applyFilters();
            });
        }

        if (searchClear) {
            searchClear.addEventListener('click', () => {
                if (searchInput) {
                    searchInput.value = '';
                    this.searchQuery = '';
                    searchClear.style.display = 'none';
                    this.applyFilters();
                    searchInput.focus();
                }
            });
        }

        // Sort select
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.applyFilters();
            });
        }

        // Filter dropdowns
        this.setupFilterDropdowns();

        // Close action menus on outside click
        document.addEventListener('click', (e) => {
            if (this.openActionMenu && !e.target.closest('.card-more-btn') && !e.target.closest('.course-actions-menu')) {
                this.closeActionMenu();
            }
        });

        // Pagination
        const prevPage = document.getElementById('prevPage');
        const nextPage = document.getElementById('nextPage');

        if (prevPage) {
            prevPage.addEventListener('click', () => this.changePage(-1));
        }
        if (nextPage) {
            nextPage.addEventListener('click', () => this.changePage(1));
        }
    }

    setupFilterDropdowns() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filterType = btn.dataset.filter;
                const menuId = 'filter' + filterType.charAt(0).toUpperCase() + filterType.slice(1);
                const menu = document.getElementById(menuId);

                document.querySelectorAll('.filter-menu.open').forEach(m => {
                    if (m !== menu) m.classList.remove('open');
                });

                if (menu) menu.classList.toggle('open');
            });
        });

        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.collectActiveFilters();
                this.applyFilters();
            });
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-dropdown')) {
                document.querySelectorAll('.filter-menu.open').forEach(m => m.classList.remove('open'));
            }
        });
    }

    collectActiveFilters() {
        this.activeFilters = { status: [], difficulty: [], category: [] };

        document.querySelectorAll('#filterStatus input:checked').forEach(cb => {
            this.activeFilters.status.push(cb.value);
        });
        document.querySelectorAll('#filterDifficulty input:checked').forEach(cb => {
            this.activeFilters.difficulty.push(cb.value);
        });
        document.querySelectorAll('#filterCategory input:checked').forEach(cb => {
            this.activeFilters.category.push(cb.value);
        });
    }

    async loadCourses() {
        console.log('Loading courses...');
        this.showSkeletons();
        this.isLoading = true;

        try {
            // Try to fetch from API if auth and baseUrl are available

                const response = await auth.authenticatedRequest(
                    baseUrl + '/api/v1/enrollment/courses/',
                    {
                        method: "GET",
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    }
                );

                if (response && response.ok) {
                    const data = await response.json();
                    console.log('API Response:', data);

                    if (data && data.results && Array.isArray(data.results)) {
                        this.allCourses = this.transformApiCourses(data.results);
                        console.log(this.allCourses)
                    } else if (Array.isArray(data)) {
                        this.allCourses = this.transformApiCourses(data);
                    } else {
                        throw new Error('Invalid response format');
                    }
                } else {
                    throw new Error('Failed to fetch courses');
                }


            this.applyFilters();

        } catch (error) {
            console.error('Failed to load courses:', error);
            this.allCourses = this.getDummyCourses();
            this.applyFilters();
        } finally {
            this.isLoading = false;
            this.hideSkeletons();
        }
    }

    transformApiCourses(apiCourses) {
        if (!Array.isArray(apiCourses)) {
            return [];
        }

        return apiCourses.map(course => {
            return {
                id: course.id || Math.random(),
                title: course.title || 'Untitled Course',
                instructor: course.instructor || 'Unknown Instructor',
                thumbnail: course.thumbnail || 'https://via.placeholder.com/600x360/4F46E5/FFFFFF?text=Course',
                status: this.mapApiStatus(course.enrollment_status),
                progress: course.progress || 0,
                difficulty: course.difficulty || 'beginner',
                category: course.category || 'uncategorized',
                duration: this.formatDuration(course.duration),
                lastAccessed: course.last_accessed ? new Date(course.last_accessed) : new Date(),
                enrolledDate: course.enrolled_at ? new Date(course.enrolled_at) : new Date(),
                completedDate: course.status === 'completed' ? new Date(course.last_accessed) : null,
                rating: course.rating || 0,
                slug: course.slug || (course.title ? course.title.toLowerCase().replace(/\s+/g, '-') : 'course-' + course.id),
                certificateId: course.certificate_id || null,
                rawData: course,
                enrollmentId:course.enrollment_id
            };
        });
    }

    mapApiStatus(apiStatus) {
        const statusMap = {
            'pending': 'in-progress',
            'in_progress': 'in-progress',
            'in-progress': 'in-progress',
            'active': 'in-progress',
            'enrolled': 'in-progress',
            'completed': 'completed',
            'finished': 'completed',
            'passed': 'completed',
            'archived': 'archived',
            'inactive': 'archived',
            'expired': 'archived'
        };

        return statusMap[apiStatus] || apiStatus || 'in-progress';
    }

    formatDuration(duration) {
        if (!duration) return '';

        if (typeof duration === 'string' && !duration.includes(':')) {
            return duration;
        }

        if (typeof duration === 'number') {
            return duration + 'm';
        }

        const parts = duration.split(':');
        if (parts.length === 3) {
            const hours = parseInt(parts[0]);
            const minutes = parseInt(parts[1]);
            const seconds = parseInt(parts[2]);

            if (hours > 0) {
                return hours + 'h ' + minutes + 'm';
            } else if (minutes > 0) {
                return minutes + 'm';
            } else {
                return seconds + 's';
            }
        }

        return duration;
    }

    getDummyCourses() {
        return [
            {
                id: 1,
                title: 'Python for Data Science',
                instructor: 'Dr. Sarah Chen',
                thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=600&h=360&fit=crop',
                status: 'in-progress',
                progress: 68,
                difficulty: 'intermediate',
                category: 'data-science',
                duration: '42h',
                lastAccessed: new Date(Date.now() - 2 * 3600000),
                enrolledDate: new Date(2026, 2, 15),
                rating: 4.7,
                slug: 'python-data-science'
            },
            {
                id: 2,
                title: 'Machine Learning A-Z',
                instructor: 'Kirill Eremenko',
                thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=360&fit=crop',
                status: 'in-progress',
                progress: 52,
                difficulty: 'beginner',
                category: 'machine-learning',
                duration: '38h',
                lastAccessed: new Date(Date.now() - 3 * 86400000),
                enrolledDate: new Date(2026, 3, 1),
                rating: 4.6,
                slug: 'machine-learning-az'
            },
            {
                id: 3,
                title: 'Deep Learning Specialization',
                instructor: 'Andrew Ng',
                thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=360&fit=crop',
                status: 'in-progress',
                progress: 22,
                difficulty: 'advanced',
                category: 'machine-learning',
                duration: '56h',
                lastAccessed: new Date(Date.now() - 7 * 86400000),
                enrolledDate: new Date(2026, 4, 10),
                rating: 4.9,
                slug: 'deep-learning-specialization'
            },
            {
                id: 4,
                title: 'Data Engineering Essentials',
                instructor: 'Alex Rivera',
                thumbnail: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=360&fit=crop',
                status: 'in-progress',
                progress: 85,
                difficulty: 'intermediate',
                category: 'data-science',
                duration: '30h',
                lastAccessed: new Date(Date.now() - 1 * 86400000),
                enrolledDate: new Date(2026, 1, 20),
                rating: 4.5,
                slug: 'data-engineering-essentials'
            },
            {
                id: 5,
                title: 'Full-Stack Web Development',
                instructor: 'Mike Johnson',
                thumbnail: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=600&h=360&fit=crop',
                status: 'in-progress',
                progress: 41,
                difficulty: 'beginner',
                category: 'web-development',
                duration: '48h',
                lastAccessed: new Date(Date.now() - 5 * 86400000),
                enrolledDate: new Date(2026, 0, 5),
                rating: 4.4,
                slug: 'fullstack-web-dev'
            },
            {
                id: 6,
                title: 'SQL for Data Analysis',
                instructor: 'Mike Johnson',
                thumbnail: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=600&h=360&fit=crop',
                status: 'completed',
                progress: 100,
                difficulty: 'beginner',
                category: 'data-science',
                duration: '18h',
                lastAccessed: new Date(2026, 4, 28),
                enrolledDate: new Date(2025, 10, 1),
                completedDate: new Date(2026, 5, 1),
                rating: 4.8,
                slug: 'sql-data-analysis',
                certificateId: 2
            }
        ];
    }

    applyFilters() {
        let courses = [...this.allCourses];

        if (this.activeTab !== 'all') {
            courses = courses.filter(c => c.status === this.activeTab);
        }

        if (this.searchQuery) {
            courses = courses.filter(c =>
                c.title.toLowerCase().includes(this.searchQuery) ||
                c.instructor.toLowerCase().includes(this.searchQuery) ||
                c.category.toLowerCase().includes(this.searchQuery)
            );
        }

        if (this.activeFilters.status.length > 0) {
            courses = courses.filter(c => this.activeFilters.status.includes(c.status));
        }

        if (this.activeFilters.difficulty.length > 0) {
            courses = courses.filter(c => this.activeFilters.difficulty.includes(c.difficulty));
        }

        if (this.activeFilters.category.length > 0) {
            courses = courses.filter(c => this.activeFilters.category.includes(c.category));
        }

        courses = this.sortCourses(courses);

        this.filteredCourses = courses;
        this.currentPage = 1;
        this.renderAll();
    }

    sortCourses(courses) {
        switch (this.sortBy) {
            case 'recent':
                return courses.sort((a, b) => {
                    const dateA = a.lastAccessed ? new Date(a.lastAccessed) : new Date(0);
                    const dateB = b.lastAccessed ? new Date(b.lastAccessed) : new Date(0);
                    return dateB - dateA;
                });
            case 'enrolled':
                return courses.sort((a, b) => {
                    const dateA = a.enrolledDate ? new Date(a.enrolledDate) : new Date(0);
                    const dateB = b.enrolledDate ? new Date(b.enrolledDate) : new Date(0);
                    return dateB - dateA;
                });
            case 'progress':
                return courses.sort((a, b) => b.progress - a.progress);
            case 'alphabetical':
                return courses.sort((a, b) => a.title.localeCompare(b.title));
            case 'rating':
                return courses.sort((a, b) => (b.rating || 0) - (a.rating || 0));
            default:
                return courses;
        }
    }

    switchTab(tab) {
        this.activeTab = tab;
        document.querySelectorAll('.learning-tab').forEach(t => t.classList.remove('active'));
        const activeTab = document.querySelector('.learning-tab[data-tab="' + tab + '"]');
        if (activeTab) activeTab.classList.add('active');
        this.applyFilters();
    }

    renderAll() {
        this.updateTabCounts();
        this.renderActiveFilters();
        this.renderResultsInfo();
        this.renderCourseGrid();
        this.renderPagination();
        this.checkEmptyState();
    }

    updateTabCounts() {
        const all = this.allCourses.length;
        const inProgress = this.allCourses.filter(c => c.status === 'in-progress').length;
        const completed = this.allCourses.filter(c => c.status === 'completed').length;
        const archived = this.allCourses.filter(c => c.status === 'archived').length;

        const countAll = document.getElementById('countAll');
        const countInProgress = document.getElementById('countInProgress');
        const countCompleted = document.getElementById('countCompleted');
        const countArchived = document.getElementById('countArchived');

        if (countAll) countAll.textContent = all;
        if (countInProgress) countInProgress.textContent = inProgress;
        if (countCompleted) countCompleted.textContent = completed;
        if (countArchived) countArchived.textContent = archived;
    }

    renderActiveFilters() {
        const container = document.getElementById('activeFilters');
        if (!container) return;

        const allFilters = [
            ...this.activeFilters.status.map(v => ({ type: 'Status', value: v })),
            ...this.activeFilters.difficulty.map(v => ({ type: 'Difficulty', value: v })),
            ...this.activeFilters.category.map(v => ({ type: 'Category', value: v }))
        ];

        if (allFilters.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = allFilters.map(f => {
            return '<span class="filter-chip">' +
                f.type + ': ' + this.capitalize(f.value) +
                '<button class="filter-chip-remove" data-type="' + f.type.toLowerCase() + '" data-value="' + f.value + '">' +
                '<i class="fas fa-times"></i>' +
                '</button>' +
                '</span>';
        }).join('') + '<button class="clear-all-filters" id="clearAllFilters">Clear all</button>';

        container.querySelectorAll('.filter-chip-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                this.removeFilter(btn.dataset.type, btn.dataset.value);
            });
        });

        const clearAllBtn = document.getElementById('clearAllFilters');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
    }

    removeFilter(type, value) {
        const map = { 'status': 'status', 'difficulty': 'difficulty', 'category': 'category' };
        const key = map[type];
        if (key) {
            this.activeFilters[key] = this.activeFilters[key].filter(v => v !== value);
            const menuId = 'filter' + key.charAt(0).toUpperCase() + key.slice(1);
            const menu = document.getElementById(menuId);
            if (menu) {
                const cb = menu.querySelector('input[value="' + value + '"]');
                if (cb) cb.checked = false;
            }
            this.applyFilters();
        }
    }

    clearAllFilters() {
        this.activeFilters = { status: [], difficulty: [], category: [] };
        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(cb => cb.checked = false);
        this.applyFilters();
    }

    renderResultsInfo() {
        const showing = this.filteredCourses.length;
        const total = this.allCourses.filter(c => this.activeTab === 'all' ? true : c.status === this.activeTab).length;

        const showingCount = document.getElementById('showingCount');
        const totalCount = document.getElementById('totalCount');

        if (showingCount) showingCount.textContent = showing;
        if (totalCount) totalCount.textContent = total;
    }

    renderCourseGrid() {
        const container = document.getElementById('courseGrid');
        if (!container) return;

        const start = (this.currentPage - 1) * this.perPage;
        const pageCourses = this.filteredCourses.slice(start, start + this.perPage);

        container.innerHTML = pageCourses.map(course => this.createCourseCard(course)).join('');

        container.querySelectorAll('.card-more-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const courseId = parseInt(btn.dataset.courseId);
                this.toggleActionMenu(courseId, btn);
            });
        });

        container.querySelectorAll('.card-continue-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const courseId = parseInt(btn.dataset.courseId);
                this.continueCourse(courseId);
            });
        });

        container.querySelectorAll('.card-cert-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const certId = parseInt(btn.dataset.certId);
                this.viewCertificate(certId);
            });
        });

        container.querySelectorAll('.card-restore-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const courseId = parseInt(btn.dataset.courseId);
                this.restoreCourse(courseId);
            });
        });


    }

    createCourseCard(course) {
        const isInProgress = course.status === 'in-progress';
        const isCompleted = course.status === 'completed';
        const isArchived = course.status === 'archived';

        let statusBadge = '';
        if (isCompleted) statusBadge = '<span class="course-card-status completed">Completed</span>';
        if (isArchived) statusBadge = '<span class="course-card-status archived">Archived</span>';

        let progressHtml = '';
        if (isInProgress) {
            progressHtml = '<div class="course-card-progress">' +
                '<div class="progress-header">' +
                '<span class="progress-label">Progress</span>' +
                '<span class="progress-percent">' + (course.progress || 0) + '%</span>' +
                '</div>' +
                '<div class="progress-bar-track">' +
                '<div class="progress-bar-fill" style="width:' + (course.progress || 0) + '%"></div>' +
                '</div>' +
                '</div>';
        }

        let footerHtml = '';
        if (isInProgress) {
            footerHtml = '<span class="last-accessed"><i class="far fa-clock"></i> ' + this.formatLastAccessed(course.lastAccessed) + '</span>' +
                '<div class="course-card-actions">' +
                '<button class="card-continue-btn" data-course-id="' + course.id + '">' +
                '<i class="fas fa-play"></i> Continue' +
                '</button>' +
                '<button class="card-more-btn" data-course-id="' + course.id + '" title="More actions">' +
                '<i class="fas fa-ellipsis-h"></i>' +
                '</button>' +
                '</div>';
        } else if (isCompleted) {
            footerHtml = '<span class="last-accessed">Completed ' + this.formatDate(course.completedDate) + '</span>' +
                '<div class="course-card-actions">' +
                '<button class="card-cert-btn" data-cert-id="' + (course.certificateId || course.id) + '">' +
                '<i class="fas fa-certificate"></i> Certificate' +
                '</button>' +
                '<button class="card-more-btn" data-course-id="' + course.id + '" title="More actions">' +
                '<i class="fas fa-ellipsis-h"></i>' +
                '</button>' +
                '</div>';
        } else if (isArchived) {
            footerHtml = '<span class="last-accessed">Archived</span>' +
                '<div class="course-card-actions">' +
                '<button class="card-restore-btn" data-course-id="' + course.id + '">' +
                '<i class="fas fa-undo"></i> Restore' +
                '</button>' +
                '<button class="card-more-btn" data-course-id="' + course.id + '" title="More actions">' +
                '<i class="fas fa-ellipsis-h"></i>' +
                '</button>' +
                '</div>';
        }

        const thumbnailUrl = course.thumbnail || 'https://via.placeholder.com/600x360/4F46E5/FFFFFF?text=Course';

        return '<div class="course-card" data-slug="' + course.slug + '" data-course-id="' + course.id + '">' +
            '<div class="course-card-thumbnail">' +
            '<img src="' + thumbnailUrl + '" alt="' + course.title + '"' +
            ' onerror="this.src=\'https://via.placeholder.com/600x360/4F46E5/FFFFFF?text=Course\'">' +
            statusBadge +
            '</div>' +
            '<div class="course-card-body">' +
            '<h3 class="course-card-title">' + course.title + '</h3>' +
            '<p class="course-card-instructor">' + course.instructor + '</p>' +
            progressHtml +
            '<div class="course-card-meta">' +
            '<span class="difficulty-badge ' + course.difficulty + '">' + this.capitalize(course.difficulty) + '</span>' +
            '<span class="course-meta-item"><i class="far fa-clock"></i> ' + (course.duration || '') + '</span>' +
            '</div>' +
            '<div class="course-card-footer">' +
            footerHtml +
            '</div>' +
            '</div>' +
            '</div>';
    }

    toggleActionMenu(courseId, triggerBtn) {
        if (this.openActionMenu === courseId) {
            this.closeActionMenu();
            return;
        }

        this.closeActionMenu();
        this.openActionMenu = courseId;

        const course = this.allCourses.find(c => c.id === courseId);
        if (!course) return;

        const rect = triggerBtn.getBoundingClientRect();
        const portal = document.getElementById('actionsDropdownPortal');
        const menu = document.getElementById('courseActionsMenu');

        if (!portal || !menu) return;

        let menuItems = '<button class="action-item" data-action="view-details" data-course-id="' + courseId + '">' +
            '<i class="fas fa-info-circle"></i> View Details' +
            '</button>';

        menu.innerHTML = menuItems;
        portal.style.display = 'block';
        portal.style.top = (rect.bottom + 4) + 'px';
        portal.style.left = (rect.right - 180) + 'px';

        menu.querySelectorAll('.action-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                const id = parseInt(item.dataset.courseId);
                this.handleAction(action, id);
                this.closeActionMenu();
            });
        });
    }

    closeActionMenu() {
        this.openActionMenu = null;
        const portal = document.getElementById('actionsDropdownPortal');
        if (portal) portal.style.display = 'none';
    }

    handleAction(action, courseId) {
        const course = this.allCourses.find(c => c.id === courseId);
        switch (action) {
            case 'view-details':
                window.location.href = `/course/${course.id}/${course.slug}/`;
                break;

        }
    }

    continueCourse(courseId) {
        const course = this.allCourses.find(c => c.id === courseId);
        window.location.href = '/enrollment/' + course.enrollmentId + '/learn/';
    }

    viewCertificate(certId) {
        window.open('/certificate/' + certId + '/', '_blank');
    }

    async archiveCourse(courseId) {
        const course = this.allCourses.find(c => c.id === courseId);
        if (course) {
            course.status = 'archived';
            this.applyFilters();
            this.showToast('"' + course.title + '" has been archived');
        }
    }

    async restoreCourse(courseId) {
        const course = this.allCourses.find(c => c.id === courseId);
        if (course) {
            course.status = 'in-progress';
            this.applyFilters();
            this.showToast('"' + course.title + '" has been restored');
        }
    }

    shareCertificate(certId) {
        const url = window.location.origin + '/certificate/' + certId + '/';
        if (navigator.share) {
            navigator.share({ title: 'My Certificate', url: url });
        } else {
            navigator.clipboard.writeText(url).then(() => {
                this.showToast('Certificate link copied!');
            });
        }
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredCourses.length / this.perPage);
        const container = document.getElementById('pageNumbers');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            if (prevBtn) prevBtn.disabled = true;
            if (nextBtn) nextBtn.disabled = true;
            return;
        }

        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

        let pagesHtml = '';
        for (let i = 1; i <= totalPages; i++) {
            pagesHtml += '<button class="page-number ' + (i === this.currentPage ? 'active' : '') + '" data-page="' + i + '">' +
                i +
                '</button>';
        }
        container.innerHTML = pagesHtml;

        container.querySelectorAll('.page-number').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentPage = parseInt(btn.dataset.page);
                this.renderCourseGrid();
                this.renderPagination();
                const grid = document.getElementById('courseGrid');
                if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    }

    changePage(delta) {
        const totalPages = Math.ceil(this.filteredCourses.length / this.perPage);
        const newPage = this.currentPage + delta;
        if (newPage >= 1 && newPage <= totalPages) {
            this.currentPage = newPage;
            this.renderCourseGrid();
            this.renderPagination();
            const grid = document.getElementById('courseGrid');
            if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    checkEmptyState() {
        const grid = document.getElementById('courseGrid');
        const empty = document.getElementById('emptyState');
        const pagination = document.getElementById('pagination');

        if (this.filteredCourses.length === 0) {
            if (grid) grid.style.display = 'none';
            if (pagination) pagination.style.display = 'none';
            if (empty) {
                empty.style.display = 'block';
                empty.classList.add('visible');
            }
            this.renderEmptyState();
        } else {
            if (grid) grid.style.display = '';
            if (pagination) pagination.style.display = '';
            if (empty) {
                empty.style.display = 'none';
                empty.classList.remove('visible');
            }
        }
    }

    renderEmptyState() {
        const container = document.getElementById('emptyState');
        if (!container) return;

        let icon, title, message, showBrowseBtn = false;

        switch (this.activeTab) {
            case 'in-progress':
                icon = '📚';
                title = 'No courses in progress';
                message = 'Start learning by enrolling in a course.';
                showBrowseBtn = true;
                break;
            case 'completed':
                icon = '🏆';
                title = 'No completed courses yet';
                message = 'Finish a course to see it here and earn your certificate.';
                break;
            case 'archived':
                icon = '📦';
                title = 'No archived courses';
                message = 'Archive courses you want to hide from your active list.';
                break;
            default:
                if (this.searchQuery || this.hasActiveFilters()) {
                    icon = '🔍';
                    title = 'No courses found';
                    message = 'Try adjusting your search or filters.';
                } else {
                    icon = '🎓';
                    title = 'Start your learning journey';
                    message = 'Browse our catalog and enroll in your first course.';
                    showBrowseBtn = true;
                }
        }

        container.innerHTML = '<span class="empty-learning-icon">' + icon + '</span>' +
            '<h3>' + title + '</h3>' +
            '<p>' + message + '</p>' +
            (showBrowseBtn ? '<button class="browse-btn" onclick="window.location.href=\'/courses\'"><i class="fas fa-compass"></i> Browse Courses</button>' : '');
    }

    hasActiveFilters() {
        return this.activeFilters.status.length > 0 ||
               this.activeFilters.difficulty.length > 0 ||
               this.activeFilters.category.length > 0;
    }

    showSkeletons() {
        const grid = document.getElementById('courseGrid');
        if (grid) {
            let skeletonHtml = '';
            for (let i = 0; i < 6; i++) {
                skeletonHtml += '<div class="course-card-skeleton">' +
                    '<div class="skeleton-block skeleton-thumb"></div>' +
                    '<div class="skeleton-body">' +
                    '<div class="skeleton-line" style="width:80%;"></div>' +
                    '<div class="skeleton-line" style="width:50%;"></div>' +
                    '<div class="skeleton-line" style="width:100%;height:6px;"></div>' +
                    '<div class="skeleton-line" style="width:40%;"></div>' +
                    '</div>' +
                    '</div>';
            }
            grid.innerHTML = skeletonHtml;
        }
    }

    hideSkeletons() {
        const grid = document.getElementById('courseGrid');
        if (grid && this.allCourses.length > 0) {
            this.renderCourseGrid();
        }
    }

    forceHideLoader() {
        console.log('Force hiding loader...');

        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            console.log('Found loadingOverlay, hiding it');
            loadingOverlay.style.display = 'none';
            loadingOverlay.style.visibility = 'hidden';
            loadingOverlay.style.opacity = '0';
            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.add('d-none');
            loadingOverlay.setAttribute('hidden', 'true');
        }

        const loaderSelectors = [
            '.loader',
            '.loading',
            '.spinner',
            '.preloader',
            '.loading-overlay',
            '.loading-screen',
            '.page-loader',
            '.loader-wrapper',
            '.loading-spinner',
            '[class*="loader"]',
            '[class*="loading"]',
            '[class*="spinner"]',
            '[id*="loader"]',
            '[id*="loading"]',
            '[id*="spinner"]'
        ];

        loaderSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.opacity = '0';
                el.classList.add('hidden');
                el.classList.add('d-none');
                el.setAttribute('hidden', 'true');
            });
        });
    }

    hideLoader() {
        this.forceHideLoader();
    }

    formatDate(date) {
        if (!date) return '';
        const dateObj = date instanceof Date ? date : new Date(date);
        if (isNaN(dateObj.getTime())) return '';
        return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    formatLastAccessed(date) {
        if (!date) return '';
        const dateObj = date instanceof Date ? date : new Date(date);
        if (isNaN(dateObj.getTime())) return '';

        const now = new Date();
        const diffMs = now - dateObj;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return diffMins + 'm ago';
        if (diffHours < 24) return diffHours + 'h ago';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return diffDays + 'd ago';
        return this.formatDate(dateObj);
    }

    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).replace(/-/g, ' ');
    }

    showToast(message) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            console.warn('Toast container not found');
            return;
        }

        const toast = document.createElement('div');
        toast.className = 'toast-popup';
        toast.textContent = message;
        toastContainer.appendChild(toast);

        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// ============================================
// BOOTSTRAP
// ============================================
let myLearningPage;

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing MyLearningPage');

    try {
        myLearningPage = new MyLearningPage();
        console.log('MyLearningPage initialized successfully');
    } catch (error) {
        console.error('Failed to initialize MyLearningPage:', error);

        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
            loadingOverlay.style.visibility = 'hidden';
            loadingOverlay.style.opacity = '0';
        }
    }
});

// Global fallback: hide loader after 3 seconds
setTimeout(() => {
    console.log('Fallback: Force hiding loader after timeout');
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
        loadingOverlay.style.visibility = 'hidden';
        loadingOverlay.style.opacity = '0';
        loadingOverlay.remove();
    }
}, 3000);
