// ============================================
// INSTRUCTOR REVENUE PAGE CONTROLLER
// ============================================

class InstructorRevenuePage {
    constructor() {
        this.periodFilter = '30';
        this.data = null;
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.totalTransactions = 0;
        this.totalPages = 0;
        this.currentTransactions = [];
        this.searchTerm = '';
        this.isLoadingTransactions = false;
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadRevenue();
        this.hideLoader();
    }

    bindEvents() {

        document.getElementById('periodFilter')?.addEventListener('change', (e) => {
            this.periodFilter = e.target.value;
            this.applyFilters();
        });
        document.getElementById('exportBtn')?.addEventListener('click', () => this.exportData());

        // View All Transactions - with preventDefault
        document.getElementById('viewAllTransactions')?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.openTransactionsModal();
        });

        // Also bind to any element with class 'view-all-link' or 'view-all-transactions'
        document.querySelectorAll('.view-all-link, .view-all-transactions, [data-action="view-all-transactions"]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.openTransactionsModal();
            });
        });

        // Modal events
        document.getElementById('closeTransactionModal')?.addEventListener('click', () => this.closeTransactionsModal());
        document.getElementById('transactionModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeTransactionsModal();
        });
        document.getElementById('modalPrevPage')?.addEventListener('click', () => this.changePage(-1));
        document.getElementById('modalNextPage')?.addEventListener('click', () => this.changePage(1));

        // Transaction search in modal
        document.getElementById('transactionSearch')?.addEventListener('input', (e) => {
            this.searchTerm = e.target.value;
            this.currentPage = 1;
            this.fetchTransactions();
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeTransactionsModal();
            }
        });
    }

    async loadRevenue() {
        this.showSkeletons();

        try {
            // Fetch revenue data with period parameter
            const revenueUrl = `${baseUrl}/api/v1/instructor/revenue/?period=${this.periodFilter}`;
            const response = await auth.authenticatedRequest(
                revenueUrl,
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load revenue.");
            }

            const revenueData = await response.json();


            // Fetch first page of transactions for main display
            const transactionUrl = `${baseUrl}/api/v1/instructor/transactions/?page=1&page_size=8`;
            const transactionResponse = await auth.authenticatedRequest(
                transactionUrl,
                {
                    method: "GET",
                }
            );

            if (!transactionResponse.ok) {
                throw new Error("Failed to load transactions.");
            }

            const transactionData = await transactionResponse.json();


            // Map the API data to the expected format
            this.data = this.mapRevenueData(revenueData, transactionData);


            this.renderAll();

        } catch (error) {
            console.error("Error loading revenue:", error);
            // Use fallback dummy data if API fails
            this.data = this.getDummyRevenue(this.periodFilter);
            this.renderAll();
            this.showToast('Failed to load data. Showing sample data.');
        }
    }

    mapRevenueData(revenueData, transactionData) {
        // Map revenue summary
        const summary = {
            lifetime: {
                value: parseFloat(revenueData.revenue_summary?.lifetime?.value) || 0,
                trend: revenueData.revenue_summary?.lifetime?.trend || null,
                direction: revenueData.revenue_summary?.lifetime?.direction || null
            },
            periodRevenue: {
                value: parseFloat(revenueData.revenue_summary?.period_revenue?.value) || 0,
                trend: revenueData.revenue_summary?.period_revenue?.trend || null,
                direction: revenueData.revenue_summary?.period_revenue?.direction || null
            },
            ytd: {
                value: parseFloat(revenueData.revenue_summary?.ytd?.value) || 0,
                trend: revenueData.revenue_summary?.ytd?.trend || null,
                direction: revenueData.revenue_summary?.ytd?.direction || null
            }
        };

        // Map course breakdown
        const courseBreakdown = (revenueData.course_breakdown || []).map(item => ({
            course: item.course || 'Unknown Course',
            amount: parseFloat(item.amount) || 0
        }));

        // Map transactions
        const transactions = this.mapTransactions(transactionData.results || []);

        return {
            summary,
            courseBreakdown,
            transactions
        };
    }

    mapTransactions(transactionsData) {
        return (transactionsData || []).map(tx => ({
            id: tx.id,
            type: tx.type || 'sale',
            desc: tx.type === 'sale' ? `Course Sale - ${tx.course}` : tx.type,
            amount: parseFloat(tx.amount) || 0,
            credit: true,
            date: new Date(tx.date),
            status: this.mapTransactionStatus(tx.status),
            course: tx.course || ''
        }));
    }

    mapTransactionStatus(status) {
        const statusMap = {
            'succeeded': 'completed',
            'completed': 'completed',
            'pending': 'pending',
            'failed': 'failed',
            'refunded': 'failed'
        };
        return statusMap[status] || status || 'completed';
    }

    async fetchTransactions() {
        if (this.isLoadingTransactions) return;

        this.isLoadingTransactions = true;
        this.showModalLoading();

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.itemsPerPage
            });

            // Add search parameter if search term exists
            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }

            // Add period filter if not 'all'
            if (this.periodFilter !== 'all') {
                params.append('period', this.periodFilter);
            }

            // Fetch transactions with pagination
            const transactionUrl = `${baseUrl}/api/v1/instructor/transactions/?${params.toString()}`;
            const response = await auth.authenticatedRequest(
                transactionUrl,
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to fetch transactions.");
            }

            const transactionData = await response.json();


            // Map transactions
            this.currentTransactions = this.mapTransactions(transactionData.results || []);
            this.totalTransactions = transactionData.count || 0;
            this.totalPages = Math.ceil(this.totalTransactions / this.itemsPerPage) || 1;

            this.renderModalTransactions();

        } catch (error) {
            console.error("Error fetching transactions:", error);
            this.currentTransactions = [];
            this.totalTransactions = 0;
            this.totalPages = 1;
            this.renderModalTransactions();
            this.showToast('Failed to load transactions.');
        } finally {
            this.isLoadingTransactions = false;
        }
    }

    async applyFilters() {
        this.showSkeletons();
        await this.loadRevenue();
        this.showFilterFeedback();
    }

    renderAll() {

        this.renderSummaryCards();
        this.renderCourseBreakdown();
        this.renderTransactions();
    }

    // ============================================
    // SUMMARY CARDS
    // ============================================
    renderSummaryCards() {
        const periodLabels = {
            '7': 'Last 7 Days',
            '30': 'Last 30 Days',
            '90': 'Last 90 Days',
            '365': 'Last 12 Months',
            'all': 'All Time'
        };

        const cards = [
            { icon: '💰', key: 'lifetime', label: 'Lifetime Revenue', cls: 'primary', format: v => '$' + v.toLocaleString() },
            { icon: '📅', key: 'periodRevenue', label: periodLabels[this.periodFilter] || 'This Period', cls: 'success', format: v => '$' + v.toLocaleString() },
            { icon: '📊', key: 'ytd', label: 'Year to Date', cls: 'accent', format: v => '$' + v.toLocaleString() }
        ];

        const summaryGrid = document.getElementById('revenueSummaryGrid');
        if (summaryGrid) {
            summaryGrid.innerHTML = cards.map(c => {
                const d = this.data.summary[c.key];
                const val = c.format(d.value);
                const trend = d.trend ? `<span class="rev-card-trend ${d.direction}">${d.direction === 'up' ? '↑' : '↓'} ${Math.abs(d.trend)}%</span>` : '';
                return `<div class="rev-summary-card ${c.cls}">
                    <span class="rev-card-icon">${c.icon}</span>
                    <span class="rev-card-value">${val}</span>
                    <span class="rev-card-label">${c.label}</span>
                    ${trend}
                </div>`;
            }).join('');
        }
    }

    // ============================================
    // COURSE BREAKDOWN
    // ============================================
    renderCourseBreakdown() {
        const data = this.data.courseBreakdown;

        if (!data || data.length === 0) {
            const breakdownBody = document.getElementById('courseBreakdownBody');
            if (breakdownBody) {
                breakdownBody.innerHTML = '<p class="no-data">No course data available</p>';
            }
            return;
        }

        const max = Math.max(...data.map(d => d.amount));
        const colors = ['c1', 'c2', 'c3', 'c4', 'c1', 'c2'];

        const breakdownBody = document.getElementById('courseBreakdownBody');
        if (breakdownBody) {
            breakdownBody.innerHTML = `
                <div class="hbar-list">
                    ${data.map((d, i) => {
                        const widthPercent = max > 0 ? Math.max((d.amount / max * 100), 2) : 0;
                        const formattedAmount = d.amount >= 1000 ? `$${(d.amount/1000).toFixed(1)}K` : `$${d.amount.toFixed(2)}`;
                        return `<div class="hbar-item">
                            <span class="hbar-course">${d.course}</span>
                            <div class="hbar-track">
                                <div class="hbar-fill ${colors[i % colors.length]}" style="width:${widthPercent}%">
                                    <span class="hbar-value">${formattedAmount}</span>
                                </div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>`;
        }
    }

    // ============================================
    // TRANSACTIONS (Main page - recent 8)
    // ============================================
    renderTransactions() {
        const txs = this.data.transactions.slice(0, 8);

        // Table
        const tableBody = document.getElementById('transactionTableBody');
        if (tableBody) {
            if (txs.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No transactions found</td></tr>';
            } else {
                tableBody.innerHTML = txs.map(tx => `
                    <tr>
                        <td><span class="tx-type"><span class="tx-type-icon">💰</span> ${this.capitalize(tx.type)}</span></td>
                        <td>${tx.desc}</td>
                        <td><span class="tx-amount credit">+$${Math.abs(tx.amount).toFixed(2)}</span></td>
                        <td>${this.formatRelative(tx.date)}</td>
                        <td><span class="tx-status ${tx.status}">${this.capitalize(tx.status)}</span></td>
                    </tr>
                `).join('');
            }
        }

        // Mobile Cards
        const cardsList = document.getElementById('transactionCardsList');
        if (cardsList) {
            if (txs.length === 0) {
                cardsList.innerHTML = '<p class="no-data">No transactions found</p>';
            } else {
                cardsList.innerHTML = txs.map(tx => `
                    <div class="tx-card">
                        <span class="tx-card-type">💰</span>
                        <div class="tx-card-info">
                            <div class="tx-card-desc">${tx.desc}</div>
                            <div class="tx-card-date">${this.formatRelative(tx.date)} · <span class="tx-status ${tx.status}">${this.capitalize(tx.status)}</span></div>
                        </div>
                        <span class="tx-card-amount credit">+$${Math.abs(tx.amount).toFixed(2)}</span>
                    </div>
                `).join('');
            }
        }
    }

    // ============================================
    // TRANSACTIONS MODAL
    // ============================================
    async openTransactionsModal() {

        this.currentPage = 1;
        this.searchTerm = '';

        // Reset search input
        const searchInput = document.getElementById('transactionSearch');
        if (searchInput) searchInput.value = '';

        const modal = document.getElementById('transactionModal');
        if (modal) {
            modal.classList.add('open');
            document.body.style.overflow = 'hidden';

            // Fetch first page of transactions
            await this.fetchTransactions();
        } else {
            console.error('Transaction modal element not found!');
        }
    }

    closeTransactionsModal() {
        const modal = document.getElementById('transactionModal');
        if (modal) {
            modal.classList.remove('open');
            document.body.style.overflow = '';
        }
    }

    async changePage(direction) {
        const newPage = this.currentPage + direction;
        if (newPage < 1 || newPage > this.totalPages) return;

        this.currentPage = newPage;
        await this.fetchTransactions();
    }

    showModalLoading() {
        const modalBody = document.getElementById('modalTransactionBody');
        if (modalBody) {
            modalBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px;">
                        <div class="loading-spinner"></div>
                        <p style="margin-top: 10px; color: #6b7280;">Loading transactions...</p>
                    </td>
                </tr>
            `;
        }
    }

    renderModalTransactions() {
        const modalBody = document.getElementById('modalTransactionBody');
        if (!modalBody) return;

        if (this.currentTransactions.length === 0) {
            modalBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No transactions found</td></tr>';
        } else {
            modalBody.innerHTML = this.currentTransactions.map((tx, index) => `
                <tr>
                    <td>${(this.currentPage - 1) * this.itemsPerPage + index + 1}</td>
                    <td><span class="tx-type"><span class="tx-type-icon">💰</span> ${this.capitalize(tx.type)}</span></td>
                    <td>${tx.desc}</td>
                    <td><span class="tx-amount credit">+$${Math.abs(tx.amount).toFixed(2)}</span></td>
                    <td>${this.formatDate(tx.date)}</td>
                    <td><span class="tx-status ${tx.status}">${this.capitalize(tx.status)}</span></td>
                </tr>
            `).join('');
        }

        // Update pagination
        const pageInfo = document.getElementById('modalPageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
        }

        const prevBtn = document.getElementById('modalPrevPage');
        const nextBtn = document.getElementById('modalNextPage');
        if (prevBtn) prevBtn.disabled = this.currentPage === 1;
        if (nextBtn) nextBtn.disabled = this.currentPage === this.totalPages;

        // Update total transactions count
        const totalCount = document.getElementById('modalTotalTransactions');
        if (totalCount) {
            totalCount.textContent = `${this.totalTransactions} transactions`;
        }
    }

    exportData() {
        if (!this.data) {
            this.showToast('No data to export');
            return;
        }

        const csvRows = [];
        const periodLabels = {
            '7': 'Last 7 Days',
            '30': 'Last 30 Days',
            '90': 'Last 90 Days',
            '365': 'Last 12 Months',
            'all': 'All Time'
        };

        // Header
        csvRows.push('Revenue Export');
        csvRows.push(`Period: ${periodLabels[this.periodFilter] || this.periodFilter}`);
        csvRows.push(`Generated: ${new Date().toLocaleString()}`);
        csvRows.push('');

        // Summary
        csvRows.push('Summary');
        csvRows.push('Metric,Value,Trend');
        const summary = this.data.summary;
        csvRows.push(`Lifetime Revenue,$${summary.lifetime.value.toFixed(2)},${summary.lifetime.trend || 0}%`);
        csvRows.push(`Period Revenue,$${summary.periodRevenue.value.toFixed(2)},${summary.periodRevenue.trend || 0}%`);
        csvRows.push(`Year to Date,$${summary.ytd.value.toFixed(2)},${summary.ytd.trend || 0}%`);
        csvRows.push('');

        // Course Breakdown
        csvRows.push('Course Breakdown');
        csvRows.push('Course,Revenue');
        this.data.courseBreakdown.forEach(item => {
            csvRows.push(`${item.course},$${item.amount.toFixed(2)}`);
        });
        csvRows.push('');

        // Transactions
        csvRows.push('Transactions');
        csvRows.push('Description,Amount,Date,Status');
        this.data.transactions.forEach(tx => {
            csvRows.push(`${tx.desc},+$${Math.abs(tx.amount).toFixed(2)},${this.formatDate(tx.date)},${tx.status}`);
        });

        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `revenue_${this.periodFilter}_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        this.showToast('Revenue data exported to CSV');
    }

    showFilterFeedback() {
        const periodLabel = document.getElementById('periodFilter')?.options[document.getElementById('periodFilter')?.selectedIndex]?.text;

    }

    showSkeletons() {
        const summaryGrid = document.getElementById('revenueSummaryGrid');
        if (summaryGrid) {
            summaryGrid.innerHTML = Array(3).fill('<div class="rev-summary-card"><div class="skeleton-block" style="height:70px;"></div></div>').join('');
        }

        document.querySelectorAll('.chart-body').forEach(el => el.innerHTML = '<div class="skeleton-block" style="height:200px;"></div>');

        const tableBody = document.getElementById('transactionTableBody');
        if (tableBody) {
            tableBody.innerHTML = Array(5).fill('<tr><td colspan="5"><div class="skeleton-line" style="height:30px;"></div></td></tr>').join('');
        }
    }

    hideLoader() {
        document.getElementById('loadingOverlay')?.classList.add('hidden');
    }

    capitalize(s) {
        return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
    }

    formatDate(d) {
        if (!(d instanceof Date)) d = new Date(d);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    formatRelative(d) {
        if (!(d instanceof Date)) d = new Date(d);
        const diff = Math.floor((Date.now() - d) / 3600000);
        if (diff < 1) return 'Just now';
        if (diff < 24) return diff + 'h ago';
        const days = Math.floor(diff / 24);
        if (days === 1) return 'Yesterday';
        if (days < 7) return days + 'd ago';
        return this.formatDate(d);
    }

    showToast(m) {
        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = m;
        document.getElementById('toastContainer').appendChild(t);
        requestAnimationFrame(() => {
            t.style.opacity = '1';
            t.style.transform = 'translateY(0)';
        });
        setTimeout(() => {
            t.style.opacity = '0';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }

    // Keep dummy data methods for fallback
    getDummyRevenue(period = '30') {
        const baseData = {};

        return baseData[period] || baseData['30'];
    }

    getMonthName(monthIndex) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
        return months[monthIndex];
    }

    generateTransactions(days) {
        return this.generateTransactionsForPage(1, 8, days).transactions;
    }

    generateTransactionsForPage(page, pageSize, days, searchTerm = '') {
        const allTransactions = this.generateAllDummyTransactions();

        let filtered = allTransactions.filter(tx =>
            tx.date >= new Date(Date.now() - days * 86400000)
        );

        if (searchTerm) {
            filtered = filtered.filter(tx =>
                tx.desc.toLowerCase().includes(searchTerm.toLowerCase()) ||
                tx.course.toLowerCase().includes(searchTerm.toLowerCase()) ||
                tx.status.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        filtered.sort((a, b) => b.date - a.date);

        const totalCount = filtered.length;
        const totalPages = Math.ceil(totalCount / pageSize) || 1;
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const transactions = filtered.slice(startIndex, endIndex);

        return {
            transactions,
            totalCount,
            totalPages
        };
    }

    generateAllDummyTransactions() {
        const transactions = [];
        const courses = [
            'Python for Data Science',
            'Machine Learning A-Z',
            'Deep Learning Specialization',
            'Data Engineering Essentials',
            'SQL for Data Analysis',
            'Cloud Computing AWS',
            'Web Development Bootcamp',
            'React & Redux Mastery'
        ];
        const statuses = ['completed', 'completed', 'completed', 'pending', 'completed', 'completed', 'completed', 'failed', 'completed', 'completed'];

        for (let i = 1; i <= 500; i++) {
            const course = courses[Math.floor(Math.random() * courses.length)];
            const status = statuses[Math.floor(Math.random() * statuses.length)];
            const amount = Math.floor(Math.random() * 100) + 20 + (Math.random() * 0.99);

            const daysAgo = Math.floor(Math.random() * 365);
            const hoursAgo = Math.floor(Math.random() * 24);

            transactions.push({
                id: i,
                type: 'sale',
                desc: `Course Sale - ${course}`,
                amount: parseFloat(amount.toFixed(2)),
                credit: true,
                date: new Date(Date.now() - (daysAgo * 86400000 + hoursAgo * 3600000)),
                status: status,
                course: course
            });
        }

        return transactions;
    }
}

let instructorRevenuePage;
document.addEventListener('DOMContentLoaded', () => {
    instructorRevenuePage = new InstructorRevenuePage();
});
