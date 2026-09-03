// ============================================
// WISHLIST PAGE CONTROLLER
// ============================================

class WishlistPage {
    constructor() {
        this.searchQuery = '';
        this.activeFilters = { category: [], price: [] };
        this.sortBy = 'date-saved-desc';
        this.currentPage = 1;
        this.perPage = 6;
        this.allItems = [];
        this.filteredItems = [];
        this.selectedItems = new Set();
        this.openActionMenu = null;
        this.pendingConfirm = null;

        // Pagination state from API
        this.apiPagination = {
            count: 0,
            next: null,
            previous: null,
            totalPages: 1
        };

        this.init();
    }

    async init() {
        console.log('WishlistPage initializing...');
        this.bindEvents();

        try {
            await this.loadWishlist();
        } catch (error) {
            console.error('Error during initialization:', error);
            this.allItems = this.getDummyWishlist();
            this.applyFilters();
        } finally {
            this.forceHideLoader();
        }
    }

    // ============================================
    // EVENT BINDINGS
    // ============================================
    bindEvents() {

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu-wrapper')) {
                document.getElementById('userDropdown')?.classList.remove('open');
            }
        });

        // Search
        const searchInput = document.getElementById('wishlistSearch');
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
            searchInput.focus();
        });

        // Sort
        document.getElementById('sortSelect')?.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.applyFilters();
        });

        // Filter dropdowns
        this.setupFilterDropdowns();

        // Select All
        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });

        // Bulk Remove
        document.getElementById('bulkRemoveBtn')?.addEventListener('click', () => {
            this.bulkRemove();
        });

        // Close action menu on outside click
        document.addEventListener('click', (e) => {
            if (this.openActionMenu && !e.target.closest('.card-more-btn') && !e.target.closest('.course-actions-menu')) {
                this.closeActionMenu();
            }
        });

        // Confirm dialog
        document.getElementById('confirmCancel')?.addEventListener('click', () => this.closeConfirm());
        document.getElementById('confirmOk')?.addEventListener('click', () => this.executeConfirm());

        // Pagination
        document.getElementById('prevPage')?.addEventListener('click', () => this.changePage(-1));
        document.getElementById('nextPage')?.addEventListener('click', () => this.changePage(1));
    }

    setupFilterDropdowns() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const filterType = btn.dataset.filter;
                const menuId = filterType === 'category' ? 'filterCategory' : 'filterPrice';
                const menu = document.getElementById(menuId);

                document.querySelectorAll('.filter-menu.open').forEach(m => {
                    if (m !== menu) m.classList.remove('open');
                });

                menu?.classList.toggle('open');
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
        this.activeFilters = { category: [], price: [] };

        document.querySelectorAll('#filterCategory input:checked').forEach(cb => {
            this.activeFilters.category.push(cb.value);
        });
        document.querySelectorAll('#filterPrice input:checked').forEach(cb => {
            this.activeFilters.price.push(cb.value);
        });
    }

    // ============================================
    // DATA LOADING
    // ============================================
    async loadWishlist() {
        console.log('Loading wishlist...');
        this.showSkeletons();

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + '/api/v1/enrollment/wishlist/',
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

                // Store pagination info from API
                this.apiPagination = {
                    count: data.count || 0,
                    next: data.next,
                    previous: data.previous,
                    totalPages: Math.ceil((data.count || 0) / this.perPage)
                };

                // Map API response to our internal format
                this.allItems = (data.results || []).map(item => this.mapApiItemToWishlistItem(item));

                // Apply filters and render
                this.applyFilters();
            } else {
                throw new Error('Failed to fetch wishlist');
            }
        } catch (error) {
            console.error('Error loading wishlist:', error);
            // Fallback to dummy data if API fails
            await new Promise(resolve => setTimeout(resolve, 600));
            this.allItems = this.getDummyWishlist();
            this.applyFilters();
        }
    }

    // Map API item structure to our internal structure
    mapApiItemToWishlistItem(apiItem) {
        return {
            id: apiItem.id,
            title: apiItem.title,
            instructor: apiItem.instructor,
            thumbnail: apiItem.thumbnail,
            rating: apiItem.rating || 0,
            reviewCount: apiItem.rating_count || 0,
            difficulty: apiItem.difficulty || 'beginner',
            duration: this.formatDuration(apiItem.duration),
            price: parseFloat(apiItem.price) || 0,
            originalPrice: apiItem.original_price ? parseFloat(apiItem.original_price) : null,
            category: apiItem.category || 'uncategorized',
            dateSaved: new Date(apiItem.date_saved),
            slug: apiItem.course_slug || apiItem.course_id,
            courseId: apiItem.course_id
        };
    }

    // Format duration from "15:00:00" to "15h"
    formatDuration(durationString) {
        if (!durationString) return '0h';

        // Parse HH:MM:SS format
        const parts = durationString.split(':');
        if (parts.length === 3) {
            const hours = parseInt(parts[0]);
            const minutes = parseInt(parts[1]);

            if (hours > 0 && minutes > 0) {
                return `${hours}h ${minutes}m`;
            } else if (hours > 0) {
                return `${hours}h`;
            } else if (minutes > 0) {
                return `${minutes}m`;
            } else {
                return '0h';
            }
        }

        // If already in short format like "15h" or "15 hours"
        return durationString;
    }

    // ============================================
    // DUMMY DATA (DELETE WHEN ENDPOINTS EXIST)
    // ============================================
    getDummyWishlist() {
        const now = Date.now();
        return [
            {
                id: 1, title: 'Advanced Machine Learning', instructor: 'Dr. Sarah Chen',
                thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600&h=340&fit=crop',
                rating: 4.8, reviewCount: 2400, difficulty: 'intermediate', duration: '48h',
                price: 49.99, originalPrice: 79.99, category: 'machine-learning',
                dateSaved: new Date(now - 2 * 86400000), slug: 'advanced-ml'
            },
            {
                id: 2, title: 'Full-Stack Web Development Bootcamp', instructor: 'Mike Johnson',
                thumbnail: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=600&h=340&fit=crop',
                rating: 4.6, reviewCount: 1800, difficulty: 'beginner', duration: '52h',
                price: 0, originalPrice: null, category: 'web-development',
                dateSaved: new Date(now - 5 * 86400000), slug: 'fullstack-web-bootcamp'
            },
            {
                id: 3, title: 'NLP with Transformers', instructor: 'Dr. Emily Wong',
                thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&h=340&fit=crop',
                rating: 4.7, reviewCount: 890, difficulty: 'advanced', duration: '36h',
                price: 44.99, originalPrice: 59.99, category: 'machine-learning',
                dateSaved: new Date(now - 3 * 86400000), slug: 'nlp-transformers'
            },
            {
                id: 4, title: 'Computer Vision Mastery', instructor: 'Prof. James Kim',
                thumbnail: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&h=340&fit=crop',
                rating: 4.9, reviewCount: 3100, difficulty: 'advanced', duration: '40h',
                price: 54.99, originalPrice: 89.99, category: 'machine-learning',
                dateSaved: new Date(now - 7 * 86400000), slug: 'computer-vision-mastery'
            },
            {
                id: 5, title: 'Reinforcement Learning Specialization', instructor: 'Dr. David Silver',
                thumbnail: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&h=340&fit=crop',
                rating: 4.8, reviewCount: 1500, difficulty: 'advanced', duration: '44h',
                price: 0, originalPrice: null, category: 'machine-learning',
                dateSaved: new Date(now - 1 * 86400000), slug: 'reinforcement-learning'
            },
            {
                id: 6, title: 'AWS Cloud Architecture', instructor: 'Priya Patel',
                thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=340&fit=crop',
                rating: 4.5, reviewCount: 2100, difficulty: 'intermediate', duration: '38h',
                price: 39.99, originalPrice: 69.99, category: 'cloud',
                dateSaved: new Date(now - 10 * 86400000), slug: 'aws-cloud-architecture'
            },
            {
                id: 7, title: 'iOS App Development with SwiftUI', instructor: 'Alex Rivera',
                thumbnail: 'https://images.unsplash.com/photo-1621839673705-6617adf9e890?w=600&h=340&fit=crop',
                rating: 4.7, reviewCount: 1200, difficulty: 'intermediate', duration: '45h',
                price: 59.99, originalPrice: 94.99, category: 'mobile',
                dateSaved: new Date(now - 14 * 86400000), slug: 'ios-swiftui'
            }
        ];
    }

    // ============================================
    // FILTERING & SORTING
    // ============================================
    applyFilters() {
        let items = [...this.allItems];

        // Search
        if (this.searchQuery) {
            items = items.filter(item =>
                item.title.toLowerCase().includes(this.searchQuery) ||
                item.instructor.toLowerCase().includes(this.searchQuery) ||
                item.category.toLowerCase().includes(this.searchQuery)
            );
        }

        // Category filter
        if (this.activeFilters.category.length > 0) {
            items = items.filter(item => this.activeFilters.category.includes(item.category));
        }

        // Price filter
        if (this.activeFilters.price.length > 0) {
            items = items.filter(item => {
                for (const pf of this.activeFilters.price) {
                    if (pf === 'free' && item.price === 0) return true;
                    if (pf === 'paid' && item.price > 0) return true;
                    if (pf === 'under-25' && item.price > 0 && item.price < 25) return true;
                    if (pf === '25-50' && item.price >= 25 && item.price <= 50) return true;
                    if (pf === 'over-50' && item.price > 50) return true;
                }
                return false;
            });
        }

        // Sort
        items = this.sortItems(items);

        this.filteredItems = items;
        this.selectedItems.clear();
        this.currentPage = 1;
        this.renderAll();
    }

    sortItems(items) {
        switch (this.sortBy) {
            case 'date-saved-desc':
                return items.sort((a, b) => new Date(b.dateSaved) - new Date(a.dateSaved));
            case 'date-saved-asc':
                return items.sort((a, b) => new Date(a.dateSaved) - new Date(b.dateSaved));
            case 'price-asc':
                return items.sort((a, b) => a.price - b.price);
            case 'price-desc':
                return items.sort((a, b) => b.price - a.price);
            case 'rating-desc':
                return items.sort((a, b) => b.rating - a.rating);
            case 'alpha-asc':
                return items.sort((a, b) => a.title.localeCompare(b.title));
            default:
                return items;
        }
    }

    // ============================================
    // RENDER ALL
    // ============================================
    renderAll() {
        this.renderActiveFilterChips();
        this.renderResultsInfo();
        this.renderWishlistGrid();
        this.renderPagination();
        this.checkEmptyState();
        this.updateBulkBar();
    }

    renderActiveFilterChips() {
        const container = document.getElementById('activeFilters');
        if (!container) return;

        const allFilters = [
            ...this.activeFilters.category.map(v => ({ type: 'Category', value: v })),
            ...this.activeFilters.price.map(v => ({ type: 'Price', value: v }))
        ];

        if (allFilters.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = allFilters.map(f => `
            <span class="filter-chip">
                ${f.type}: ${this.capitalize(f.value.replace(/-/g, ' '))}
                <button class="filter-chip-remove" data-type="${f.type.toLowerCase()}" data-value="${f.value}">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        `).join('') + '<button class="clear-all-filters" id="clearAllFilters">Clear all</button>';

        container.querySelectorAll('.filter-chip-remove').forEach(btn => {
            btn.addEventListener('click', () => this.removeFilter(btn.dataset.type, btn.dataset.value));
        });
        document.getElementById('clearAllFilters')?.addEventListener('click', () => this.clearAllFilters());
    }

    removeFilter(type, value) {
        const map = { 'category': 'category', 'price': 'price' };
        const key = map[type];
        if (key) {
            this.activeFilters[key] = this.activeFilters[key].filter(v => v !== value);
            const menuId = key === 'category' ? 'filterCategory' : 'filterPrice';
            const cb = document.querySelector(`#${menuId} input[value="${value}"]`);
            if (cb) cb.checked = false;
            this.applyFilters();
        }
    }

    clearAllFilters() {
        this.activeFilters = { category: [], price: [] };
        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(cb => cb.checked = false);
        this.applyFilters();
    }

    renderResultsInfo() {
        const showingCount = document.getElementById('showingCount');
        const totalSaved = document.getElementById('totalSaved');

        if (showingCount) {
            showingCount.textContent = this.filteredItems.length;
        }
        if (totalSaved) {
            totalSaved.textContent = this.allItems.length > 0 ? `(${this.allItems.length} total)` : '';
        }
    }

    // ============================================
    // RENDER WISHLIST GRID
    // ============================================
    renderWishlistGrid() {
        const container = document.getElementById('wishlistGrid');
        if (!container) return;

        const start = (this.currentPage - 1) * this.perPage;
        const pageItems = this.filteredItems.slice(start, start + this.perPage);

        container.innerHTML = pageItems.map(item => this.createWishlistCard(item)).join('');

        // Bind card events
        container.querySelectorAll('.card-select-checkbox').forEach(cb => {
            cb.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(cb.dataset.id);
                if (cb.checked) this.selectedItems.add(id);
                else this.selectedItems.delete(id);
                this.updateBulkBar();
                cb.closest('.wishlist-card')?.classList.toggle('selected', cb.checked);
            });
        });

        container.querySelectorAll('.card-heart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                this.confirmRemove(id);
            });
        });

        container.querySelectorAll('.enroll-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                this.enrollCourse(id);
            });
        });

        container.querySelectorAll('.card-more-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                this.toggleActionMenu(id, btn);
            });
        });

        // Card thumbnail/body click -> navigate to course
        container.querySelectorAll('.wishlist-card-thumbnail, .wishlist-card-body').forEach(el => {
            el.addEventListener('click', (e) => {
                if (e.target.closest('button')) return;
                const card = el.closest('.wishlist-card');
                const slug = card?.dataset.slug;
                if (slug) window.location.href = `/course/${slug}`;
            });
        });
    }

    createWishlistCard(item) {
        return `
            <div class="wishlist-card" data-id="${item.id}" data-slug="${item.slug}">
                <input type="checkbox" class="card-select-checkbox" data-id="${item.id}">
                <div class="wishlist-card-thumbnail">
                    <img src="${item.thumbnail}" alt="${item.title}"
                         onerror="this.src='https://via.placeholder.com/600x340/4F46E5/FFFFFF?text=Course'">
                    <button class="card-heart-btn" data-id="${item.id}" title="Remove from wishlist">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <div class="wishlist-card-body">
                    <h3 class="wishlist-card-title">${item.title}</h3>
                    <p class="wishlist-card-instructor">${item.instructor}</p>
                    <div class="wishlist-card-meta">
                        <span class="wishlist-rating"><i class="fas fa-star"></i> ${item.rating || 'N/A'}</span>
                        <span class="wishlist-review-count">(${this.formatNumber(item.reviewCount || 0)})</span>
                        <span class="difficulty-badge ${item.difficulty}">${this.capitalize(item.difficulty)}</span>
                        <span class="wishlist-duration"><i class="far fa-clock"></i> ${item.duration}</span>
                    </div>
                    <div class="wishlist-price-row">
                        <span class="wishlist-price ${item.price === 0 ? 'free' : ''}">
                            ${item.price === 0 ? 'Free' : '$' + item.price.toFixed(2)}
                        </span>
                        ${item.originalPrice ? `<span class="original-price">$${item.originalPrice.toFixed(2)}</span>` : ''}
                    </div>
                    <div class="date-saved">
                        <i class="far fa-clock"></i> Saved ${this.formatRelativeTime(item.dateSaved)}
                    </div>
                    <div class="wishlist-card-footer">
                        <button class="enroll-btn" data-id="${item.id}">
                            <i class="fas fa-rocket"></i> Enroll Now
                        </button>
                        <button class="card-more-btn" data-id="${item.id}" title="More actions">
                            <i class="fas fa-ellipsis-h"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================================
    // SELECTION & BULK ACTIONS
    // ============================================
    toggleSelectAll(checked) {
        const start = (this.currentPage - 1) * this.perPage;
        const pageItems = this.filteredItems.slice(start, start + this.perPage);

        if (checked) {
            pageItems.forEach(item => this.selectedItems.add(item.id));
        } else {
            pageItems.forEach(item => this.selectedItems.delete(item.id));
        }

        document.querySelectorAll('.card-select-checkbox').forEach(cb => {
            cb.checked = checked;
            cb.closest('.wishlist-card')?.classList.toggle('selected', checked);
        });
        this.updateBulkBar();
    }

    updateBulkBar() {
        const bar = document.getElementById('bulkActionsBar');
        const count = this.selectedItems.size;
        const btn = document.getElementById('bulkRemoveBtn');
        const selectAll = document.getElementById('selectAllCheckbox');
        const countEl = document.getElementById('bulkSelectedCount');

        if (!bar || !btn || !selectAll || !countEl) return;

        if (this.filteredItems.length === 0) {
            bar.style.display = 'none';
            return;
        }

        bar.style.display = 'flex';
        countEl.textContent = `${count} course${count !== 1 ? 's' : ''} selected`;
        btn.disabled = count === 0;

        // Update select all checkbox state
        const start = (this.currentPage - 1) * this.perPage;
        const pageItems = this.filteredItems.slice(start, start + this.perPage);
        const allPageSelected = pageItems.length > 0 && pageItems.every(item => this.selectedItems.has(item.id));
        selectAll.checked = allPageSelected;
        selectAll.indeterminate = count > 0 && !allPageSelected;
    }

    async bulkRemove() {
        if (this.selectedItems.size === 0) return;

        const selectedCount = this.selectedItems.size;

        this.showConfirm(
            'Remove selected courses?',
            `Are you sure you want to remove ${selectedCount} course${selectedCount !== 1 ? 's' : ''} from your wishlist?`,
            async () => {
                try {
                    // Real API call for bulk removal
                    for (const id of this.selectedItems) {
                        const response = await auth.authenticatedRequest(
                            `${baseUrl}/api/v1/courses/wishlist/${id}/remove/`,
                            {
                                method: "DELETE",
                                headers: {
                                    'Content-Type': 'application/json',
                                }
                            }
                        );

                        if (!response || !response.ok) {
                            console.warn(`Failed to remove item ${id}`);
                        }
                    }

                    // Remove from local state
                    this.allItems = this.allItems.filter(item => !this.selectedItems.has(item.id));
                    this.selectedItems.clear();
                    this.applyFilters();
                    this.showToast(`${selectedCount} course(s) removed`);
                } catch (error) {
                    console.error('Error during bulk removal:', error);
                    this.showToast('Failed to remove some items');
                }
            }
        );
    }

    // ============================================
    // SINGLE COURSE ACTIONS
    // ============================================
    confirmRemove(id) {
        const item = this.allItems.find(i => i.id === id);
        if (!item) return;

        this.showConfirm(
            'Remove from wishlist?',
            `"${item.title}" will be removed from your wishlist.`,
            async () => {
                try {
                    // Real API call for single removal
                    const response = await auth.authenticatedRequest(
                        `${baseUrl}/api/v1/courses/wishlist/${id}/remove/`,
                        {
                            method: "DELETE",
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        }
                    );

                    if (!response || !response.ok) {
                        throw new Error('Failed to remove item');
                    }

                    this.allItems = this.allItems.filter(i => i.id !== id);
                    this.selectedItems.delete(id);
                    this.applyFilters();
                    this.showToast(`"${item.title}" removed from wishlist`);
                } catch (error) {
                    console.error('Error removing item:', error);
                    this.showToast('Failed to remove item');
                }
            }
        );
    }

    enrollCourse(id) {
        const item = this.allItems.find(i => i.id === id);
        if (item) {
            window.location.href = `/course/${item.slug}/enroll/`;
        }
    }

    // ============================================
    // ACTION MENU
    // ============================================
    toggleActionMenu(id, triggerBtn) {
        if (this.openActionMenu === id) {
            this.closeActionMenu();
            return;
        }

        this.closeActionMenu();
        this.openActionMenu = id;

        const item = this.allItems.find(i => i.id === id);
        if (!item) return;

        const rect = triggerBtn.getBoundingClientRect();
        const portal = document.getElementById('actionsDropdownPortal');
        const menu = document.getElementById('courseActionsMenu');

        if (!portal || !menu) return;

        menu.innerHTML = `
            <button class="action-item" data-action="copy-link" data-id="${id}">
                <i class="fas fa-link"></i> Copy Course Link
            </button>
            <button class="action-item danger" data-action="remove" data-id="${id}">
                <i class="fas fa-trash-alt"></i> Remove from Wishlist
            </button>
        `;

        portal.style.display = 'block';
        const menuHeight = 140;
        const top = rect.bottom + 4 + menuHeight > window.innerHeight ? rect.top - menuHeight - 4 : rect.bottom + 4;
        portal.style.top = `${top}px`;
        portal.style.left = `${Math.min(rect.right - 190, window.innerWidth - 200)}px`;

        menu.querySelectorAll('.action-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                const courseId = parseInt(item.dataset.id);
                this.handleMenuAction(action, courseId);
                this.closeActionMenu();
            });
        });
    }

    closeActionMenu() {
        this.openActionMenu = null;
        const portal = document.getElementById('actionsDropdownPortal');
        if (portal) {
            portal.style.display = 'none';
        }
    }

    handleMenuAction(action, id) {
        switch (action) {
            case 'copy-link': this.copyCourseLink(id); break;
            case 'remove': this.confirmRemove(id); break;
        }
    }

    shareCourse(id) {
        const item = this.allItems.find(i => i.id === id);
        if (!item) return;
        const url = `${window.location.origin}/course/${item.slug}`;
        if (navigator.share) {
            navigator.share({ title: item.title, url });
        } else {
            navigator.clipboard.writeText(url).then(() => this.showToast('Course link copied!'));
        }
    }

    copyCourseLink(id) {
        const item = this.allItems.find(i => i.id === id);
        if (!item) return;
        console.log(item)
        const url = `${window.location.origin}/course/${item.courseId}/${item.slug}/`;
        navigator.clipboard.writeText(url).then(() => this.showToast('Link copied to clipboard!'));
    }

    // ============================================
    // CONFIRM DIALOG
    // ============================================
    showConfirm(title, message, onConfirm) {
        const confirmTitle = document.getElementById('confirmTitle');
        const confirmMessage = document.getElementById('confirmMessage');
        const confirmOverlay = document.getElementById('confirmOverlay');

        if (!confirmTitle || !confirmMessage || !confirmOverlay) return;

        confirmTitle.textContent = title;
        confirmMessage.textContent = message;
        confirmOverlay.style.display = 'flex';
        this.pendingConfirm = onConfirm;
    }

    closeConfirm() {
        const confirmOverlay = document.getElementById('confirmOverlay');
        if (confirmOverlay) {
            confirmOverlay.style.display = 'none';
        }
        this.pendingConfirm = null;
    }

    executeConfirm() {
        if (this.pendingConfirm) {
            this.pendingConfirm();
        }
        this.closeConfirm();
    }

    // ============================================
    // PAGINATION
    // ============================================
    renderPagination() {
        const totalPages = Math.ceil(this.filteredItems.length / this.perPage);
        const container = document.getElementById('pageNumbers');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (!container || !prevBtn || !nextBtn) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            prevBtn.disabled = true;
            nextBtn.disabled = true;
            return;
        }

        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= totalPages;

        let html = '';
        for (let i = 1; i <= totalPages; i++) {
            html += `<button class="page-number ${i === this.currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        container.innerHTML = html;

        container.querySelectorAll('.page-number').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentPage = parseInt(btn.dataset.page);
                this.renderWishlistGrid();
                this.renderPagination();
                this.updateBulkBar();
                document.getElementById('wishlistGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    }

    changePage(delta) {
        const totalPages = Math.ceil(this.filteredItems.length / this.perPage);
        const newPage = this.currentPage + delta;
        if (newPage >= 1 && newPage <= totalPages) {
            this.currentPage = newPage;
            this.renderWishlistGrid();
            this.renderPagination();
            this.updateBulkBar();
            document.getElementById('wishlistGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    checkEmptyState() {
        const grid = document.getElementById('wishlistGrid');
        const empty = document.getElementById('emptyState');
        const pagination = document.getElementById('pagination');
        const bulkBar = document.getElementById('bulkActionsBar');
        const resultsInfo = document.getElementById('resultsInfo');

        if (!grid || !empty || !pagination || !bulkBar || !resultsInfo) return;

        if (this.filteredItems.length === 0) {
            grid.style.display = 'none';
            pagination.style.display = 'none';
            bulkBar.style.display = 'none';
            resultsInfo.style.display = 'none';
            empty.style.display = 'block';
        } else {
            grid.style.display = '';
            pagination.style.display = '';
            resultsInfo.style.display = '';
            empty.style.display = 'none';
        }
    }

    // ============================================
    // SKELETONS AND LOADER
    // ============================================
    showSkeletons() {
        const grid = document.getElementById('wishlistGrid');
        if (grid) {
            grid.innerHTML = Array(6).fill(`
                <div class="wishlist-card-skeleton">
                    <div class="skeleton-block skeleton-thumb"></div>
                    <div class="skeleton-body">
                        <div class="skeleton-line" style="width:80%;"></div>
                        <div class="skeleton-line" style="width:50%;"></div>
                        <div class="skeleton-line" style="width:60%;"></div>
                        <div class="skeleton-line" style="width:30%;"></div>
                    </div>
                </div>
            `).join('');
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

    // ============================================
    // UTILITIES
    // ============================================
    formatDate(date) {
        if (!date) return '';
        return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    formatRelativeTime(date) {
        if (!date) return '';
        const now = new Date();
        const diffMs = now - new Date(date);
        const diffDays = Math.floor(diffMs / 86400000);
        const diffWeeks = Math.floor(diffDays / 7);

        if (diffDays < 1) return 'today';
        if (diffDays === 1) return 'yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffWeeks === 1) return '1 week ago';
        if (diffWeeks < 4) return `${diffWeeks} weeks ago`;
        return this.formatDate(date);
    }

    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toString();
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
let wishlistPage;

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing WishlistPage');

    try {
        wishlistPage = new WishlistPage();
        console.log('WishlistPage initialized successfully');
    } catch (error) {
        console.error('Failed to initialize WishlistPage:', error);

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
