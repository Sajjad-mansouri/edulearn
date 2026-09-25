// ============================================
// DYNAMIC FILTERS LOADER
// Works for both Catalog and Category pages
// Supports category -> subcategory hierarchy
// ============================================


class FiltersLoader {
    constructor(options = {}) {
        this.containerId = options.containerId || 'catalogFilters';
        this.filtersEndpoint = options.filtersEndpoint || '/api/filters/';
        this.category = options.category || null;
        this.includeCategories = options.includeCategories !== false; // Show categories with subcategories
        this.container = null;
        this.expandedCategory = null; // Track which category is expanded
        this.init();
    }

    init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.warn(`Filters container #${this.containerId} not found`);
            return;
        }
        this.loadFilters();
    }

    async loadFilters() {
        try {
            // ==========================================
            // REAL API CALL - Uncomment for production
            // ==========================================
            // const url = this.category
            //     ? `${this.filtersEndpoint}?category=${this.category}`
            //     : this.filtersEndpoint;
            // const response = await fetch(url);
            // if (!response.ok) throw new Error('Failed to fetch filters');
            // const data = await response.json();
            // this.renderAllFilters(data);
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/courses/filters/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) throw new Error('Failed to fetch filters');
            const data = await response.json()
            this.renderAllFilters(data);



        } catch (error) {
            console.error('Error loading filters:', error);

        }
    }



    renderAllFilters(data) {
        if (!this.container) return;

        let html = '';

        // Header
        html += `
            <div class="filters-header">
                <h3>Filters</h3>
                <button class="clear-filters-btn" id="clearFiltersBtn">Clear All</button>
            </div>
        `;

        // Category Filter with expandable subcategories
        if (this.includeCategories && data.categories && data.categories.length > 0) {
            html += this.renderCategoryFilter(data.categories);
        }

        // Rating Filter
        html += this.renderFilterSection('Rating', 'rating', data.ratings, false, true);

        // Level Filter
        html += this.renderFilterSection('Level', 'level', data.levels, false);

        // Price Filter
        html += this.renderFilterSection('Price', 'price', data.prices, false);

        // Duration Filter
        html += this.renderFilterSection('Duration', 'duration', data.durations, false);

        // Language Filter
        html += this.renderFilterSection('Language', 'language', data.languages, false);

        this.container.innerHTML = html;

        // Bind events after rendering
        this.bindEvents();
        this.bindCategoryEvents();
    }

    renderCategoryFilter(categories) {
        let html = `
            <div class="filter-section">
                <h4 class="filter-title">Category</h4>
                <div class="category-filter-list">
        `;

        categories.forEach(category => {
            const isExpanded = this.expandedCategory === category.value;
            const expandedClass = isExpanded ? ' expanded' : '';

            html += `
                <div class="category-filter-item">
                    <div class="category-filter-header ${expandedClass}" data-category="${category.value}">
                        <label class="filter-check category-check">
                            <input type="checkbox" value="${category.value}" class="filter-input category-input" data-filter="category">
                            <span class="checkmark"></span>
                            <i class="fas ${category.icon} category-icon"></i>
                            <span class="filter-label-text">${this.escapeHtml(category.label)}</span>
                            <span class="filter-count">${this.formatCount(category.count)}</span>
                        </label>
                        <button class="category-expand-btn" data-category="${category.value}">
                            <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'}"></i>
                        </button>
                    </div>
                    <div class="category-subcategories ${isExpanded ? 'show' : ''}" data-category="${category.value}">
                        <div class="subcategory-select-all">
                            <label class="filter-check">
                                <input type="checkbox" value="all-${category.value}" class="filter-input subcategory-all" data-filter="subcategory" data-category="${category.value}">
                                <span class="checkmark"></span>
                                <span class="filter-label-text">All ${this.escapeHtml(category.label)}</span>
                            </label>
                        </div>
            `;

            category.subcategories.forEach(sub => {
                html += `
                    <label class="filter-check subcategory-check" data-parent="${category.value}">
                        <input type="checkbox" value="${sub.value}" class="filter-input subcategory-input" data-filter="subcategory" data-category="${category.value}">
                        <span class="checkmark"></span>
                        <span class="filter-label-text">${this.escapeHtml(sub.label)}</span>
                        <span class="filter-count">${this.formatCount(sub.count)}</span>
                    </label>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    renderFilterSection(title, filterType, items, showCount = false, showStars = false) {
        let section = `
            <div class="filter-section">
                <h4 class="filter-title">${this.escapeHtml(title)}</h4>
        `;

        items.forEach(item => {
            const checked = item.default ? ' checked' : '';
            const countHtml = showCount && item.count ? `<span class="filter-count">${this.formatCount(item.count)}</span>` : '';
            const starsHtml = showStars ? `<span class="filter-stars">${this.getStars(item.stars)}</span>` : '';

            section += `
                <label class="filter-check">
                    <input type="checkbox" value="${item.value}" class="filter-input" data-filter="${filterType}"${checked}>
                    <span class="checkmark"></span>
                    ${starsHtml}
                    <span class="filter-label-text">${this.escapeHtml(item.label)}</span>
                    ${countHtml}
                </label>
            `;
        });

        section += `</div>`;
        return section;
    }

    bindCategoryEvents() {
        // Category expand/collapse
        this.container.querySelectorAll('.category-expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const categoryValue = btn.dataset.category;

                // Toggle expanded state
                if (this.expandedCategory === categoryValue) {
                    this.expandedCategory = null;
                } else {
                    this.expandedCategory = categoryValue;
                }

                // Re-render categories to update UI
                const categoryHeader = btn.closest('.category-filter-header');
                const subcategoriesContainer = btn.closest('.category-filter-item').querySelector('.category-subcategories');
                const icon = btn.querySelector('i');

                categoryHeader.classList.toggle('expanded');
                subcategoriesContainer.classList.toggle('show');

                if (categoryHeader.classList.contains('expanded')) {
                    icon.className = 'fas fa-chevron-down';
                } else {
                    icon.className = 'fas fa-chevron-right';
                }
            });
        });

        // Category header click (also expands)
        this.container.querySelectorAll('.category-filter-header').forEach(header => {
            header.addEventListener('click', (e) => {
                // Don't toggle if clicking on checkbox
                if (e.target.type === 'checkbox') return;

                const expandBtn = header.querySelector('.category-expand-btn');
                if (expandBtn) {
                    expandBtn.click();
                }
            });
        });

        // "Select All" for subcategories
        this.container.querySelectorAll('.subcategory-all').forEach(selectAll => {
            selectAll.addEventListener('change', (e) => {
                const categoryValue = e.target.dataset.category;
                const subcategoryCheckboxes = this.container.querySelectorAll(
                    `.subcategory-input[data-category="${categoryValue}"]`
                );

                subcategoryCheckboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                });

                // If selecting all, also check the parent category
                const categoryCheckbox = this.container.querySelector(
                    `.category-input[value="${categoryValue}"]`
                );
                if (categoryCheckbox) {
                    categoryCheckbox.checked = e.target.checked;
                }

                this.dispatchFilterEvent();
            });
        });

        // Individual subcategory selection
        this.container.querySelectorAll('.subcategory-input').forEach(subInput => {
            subInput.addEventListener('change', () => {
                const categoryValue = subInput.dataset.category;

                // Update "Select All" checkbox
                const allSubcategories = this.container.querySelectorAll(
                    `.subcategory-input[data-category="${categoryValue}"]`
                );
                const selectAll = this.container.querySelector(
                    `.subcategory-all[data-category="${categoryValue}"]`
                );

                if (selectAll) {
                    const allChecked = Array.from(allSubcategories).every(cb => cb.checked);
                    const noneChecked = Array.from(allSubcategories).every(cb => !cb.checked);

                    if (allChecked) {
                        selectAll.checked = true;
                        selectAll.indeterminate = false;
                    } else if (noneChecked) {
                        selectAll.checked = false;
                        selectAll.indeterminate = false;
                    } else {
                        selectAll.checked = false;
                        selectAll.indeterminate = true;
                    }
                }

                // Update parent category checkbox
                const categoryCheckbox = this.container.querySelector(
                    `.category-input[value="${categoryValue}"]`
                );
                if (categoryCheckbox) {
                    const anyChecked = Array.from(allSubcategories).some(cb => cb.checked);
                    categoryCheckbox.checked = anyChecked;
                }

                this.dispatchFilterEvent();
            });
        });

        // Parent category checkbox
        this.container.querySelectorAll('.category-input').forEach(catInput => {
            catInput.addEventListener('change', (e) => {
                const categoryValue = e.target.value;
                const subcategoryCheckboxes = this.container.querySelectorAll(
                    `.subcategory-input[data-category="${categoryValue}"]`
                );
                const selectAll = this.container.querySelector(
                    `.subcategory-all[data-category="${categoryValue}"]`
                );

                subcategoryCheckboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                });

                if (selectAll) {
                    selectAll.checked = e.target.checked;
                }

                this.dispatchFilterEvent();
            });
        });
    }

    bindEvents() {
        // Clear filters button
        const clearBtn = this.container.querySelector('#clearFiltersBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Regular filter checkboxes (non-category)
        this.container.querySelectorAll('.filter-input:not(.category-input):not(.subcategory-input):not(.subcategory-all)').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.dispatchFilterEvent();
            });
        });
    }

    dispatchFilterEvent() {
        const event = new CustomEvent('filtersChanged', {
            detail: {
                containerId: this.containerId,
                filters: this.getActiveFilters()
            }
        });
        document.dispatchEvent(event);
    }

    getActiveFilters() {
        const filters = {
            categories: [],
            subcategories: [],
            ratings: [],
            levels: [],
            prices: [],
            durations: [],
            languages: []
        };

        this.container.querySelectorAll('.filter-input:checked').forEach(cb => {
            const filterType = cb.dataset.filter;
            if (filters[filterType + 's'] || filters[filterType]) {
                const target = filters[filterType + 's'] || filters[filterType];
                if (target) {
                    target.push(cb.value);
                }
            }
        });

        return filters;
    }

    clearAllFilters() {
        this.container.querySelectorAll('.filter-input').forEach(cb => {
            cb.checked = false;
        });

        // Re-check default checkboxes
        this.container.querySelectorAll('.filter-input[checked]').forEach(cb => {
            cb.checked = true;
        });

        // Reset indeterminate states
        this.container.querySelectorAll('.subcategory-all').forEach(cb => {
            cb.indeterminate = false;
        });

        // Collapse all categories
        this.expandedCategory = null;
        this.container.querySelectorAll('.category-subcategories').forEach(el => {
            el.classList.remove('show');
        });
        this.container.querySelectorAll('.category-filter-header').forEach(el => {
            el.classList.remove('expanded');
        });
        this.container.querySelectorAll('.category-expand-btn i').forEach(icon => {
            icon.className = 'fas fa-chevron-right';
        });

        // Dispatch event
        const event = new CustomEvent('filtersCleared', {
            detail: { containerId: this.containerId }
        });
        document.dispatchEvent(event);
    }

    getStars(count) {
        return '⭐'.repeat(count);
    }

    formatCount(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toString();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ============================================
// INITIALIZE
// ============================================
// For Catalog Page:
// new FiltersLoader({ containerId: 'catalogFilters', includeCategories: true });
//
// For Category Page:
// new FiltersLoader({ containerId: 'categoryFilters', category: 'programming', includeCategories: true });
