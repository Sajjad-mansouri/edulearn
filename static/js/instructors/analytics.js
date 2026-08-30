// ============================================
// INSTRUCTOR ANALYTICS PAGE CONTROLLER
// ============================================

class InstructorAnalyticsPage {
    constructor() {
        this.courseFilter = 'all';
        this.periodFilter = 'all'; // Default to all time
        this.data = null;
        this.courses = []; // Store courses list
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadCourses(); // Load courses first
        await this.loadAnalytics();
        this.hideLoader();
    }

    bindEvents() {
        document.getElementById('hamburgerBtn')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.toggle('open'));
        document.getElementById('mobileMenuBtn')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('appSidebar')?.classList.toggle('open'); });
        document.getElementById('sidebarOverlay')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.remove('open'));
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => { e.stopPropagation(); document.getElementById('userDropdown')?.classList.toggle('open'); });
        document.addEventListener('click', (e) => { if (!e.target.closest('.user-menu-wrapper')) document.getElementById('userDropdown')?.classList.remove('open'); });

        document.getElementById('courseFilter')?.addEventListener('change', (e) => {
            this.courseFilter = e.target.value;
            this.applyFilters();
        });

        document.getElementById('periodFilter')?.addEventListener('change', (e) => {
            this.periodFilter = e.target.value;
            this.applyFilters();
        });

        document.getElementById('exportBtn')?.addEventListener('click', () => this.exportCSV());
    }

    async loadCourses() {
        // ==========================================
        // REAL API CALL - Fetch courses list
        // ==========================================
        // const response = await ApiService.getInstructorCourses();
        // this.courses = response.courses;
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/analytics/courses/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load courses.");
            }

            this.courses = await response.json();




        } catch (error) {
            console.error("Error loading courses:", error);
        }


        this.populateCourseFilter();
    }

    populateCourseFilter() {
        const courseFilter = document.getElementById('courseFilter');
        if (!courseFilter) return;

        // Keep the "All Courses" option
        let optionsHTML = '<option value="all">All Courses</option>';

        // Add course options
        this.courses.forEach(course => {
            optionsHTML += `<option value="${course.slug}">${course.title}</option>`;
        });

        courseFilter.innerHTML = optionsHTML;
    }

    async loadAnalytics() {
        this.showSkeletons();

        // ==========================================
        // REAL API CALL - Fetch data based on current filters
        // ==========================================

        try {
           const kwargs = {
                period: this.periodFilter,
                course: this.courseFilter
            };

            const params = new URLSearchParams(kwargs);
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/analytics/?${params}`,
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load analytics.");
            }

            const data = await response.json();
            console.log("analytics data",data)
            this.data = data



        } catch (error) {
            console.error("Error loading analytics:", error);
        }

        // const params = {
        //     period: this.periodFilter,
        //     course: this.courseFilter
        // };
        // const data = await ApiService.getOverallAnalytics(params);
        // this.data = data;

        // await new Promise(r => setTimeout(r, 700));

        // this.data = this.getDummyAnalytics(this.periodFilter, this.courseFilter);
        this.renderAll();
    }

    // Dummy data generator that returns period-specific data
    getDummyAnalytics(period, courseFilter = 'all') {
        // This simulates what the backend would return for each period
        // In real app, this would be filtered by the backend based on course
        const analyticsData = {
            'all': {
                kpis: {
                    totalStudents: { value: 2450, trend: 12, direction: 'up' },
                    revenue: { value: 38500, trend: 18, direction: 'up' },
                    completionRate: { value: 78, trend: 5, direction: 'up' },
                    retentionRate: { value: 85, trend: 3, direction: 'up' },
                    watchTime: { value: 42000, trend: 8, direction: 'up' },
                    quizAvg: { value: 84, trend: 2, direction: 'up' }
                },
                enrollmentTrends: [
                    { label: 'Jan', count: 120 },
                    { label: 'Feb', count: 180 },
                    { label: 'Mar', count: 250 },
                    { label: 'Apr', count: 310 },
                    { label: 'May', count: 380 },
                    { label: 'Jun', count: 450 },
                    { label: 'Jul', count: 520 },
                    { label: 'Aug', count: 590 },
                    { label: 'Sep', count: 650 },
                    { label: 'Oct', count: 720 },
                    { label: 'Nov', count: 800 },
                    { label: 'Dec', count: 950 }
                ],
                revenueTrends: [
                    { label: 'Jan', amount: 2400 },
                    { label: 'Feb', amount: 3600 },
                    { label: 'Mar', amount: 5000 },
                    { label: 'Apr', amount: 6200 },
                    { label: 'May', amount: 7600 },
                    { label: 'Jun', amount: 9000 },
                    { label: 'Jul', amount: 10500 },
                    { label: 'Aug', amount: 11800 },
                    { label: 'Sep', amount: 13000 },
                    { label: 'Oct', amount: 14500 },
                    { label: 'Nov', amount: 16000 },
                    { label: 'Dec', amount: 18500 }
                ],
                completion: { completed: 1910, inProgress: 540 },
                retention: [
                    { week: 'W1', pct: 100 },
                    { week: 'W2', pct: 92 },
                    { week: 'W4', pct: 78 },
                    { week: 'W8', pct: 62 },
                    { week: 'W12', pct: 48 }
                ],
                watchTimeByCourse: [
                    { course: 'Python for Data Science', hours: 12500 },
                    { course: 'Machine Learning A-Z', hours: 8200 },
                    { course: 'Deep Learning Specialization', hours: 6800 },
                    { course: 'Data Engineering Essentials', hours: 4500 }
                ],
                quizPerformance: [
                    { course: 'Python for Data Science', avg: 86 },
                    { course: 'Machine Learning A-Z', avg: 82 },
                    { course: 'Deep Learning Specialization', avg: 88 },
                    { course: 'Data Engineering Essentials', avg: 78 }
                ],
                geoDistribution: [
                    { country: 'United States', flag: '🇺🇸', pct: 45 },
                    { country: 'India', flag: '🇮🇳', pct: 18 },
                    { country: 'United Kingdom', flag: '🇬🇧', pct: 12 },
                    { country: 'Germany', flag: '🇩🇪', pct: 8 },
                    { country: 'Canada', flag: '🇨🇦', pct: 6 },
                    { country: 'Australia', flag: '🇦🇺', pct: 4 },
                    { country: 'France', flag: '🇫🇷', pct: 3 },
                    { country: 'Others', flag: '🌍', pct: 4 }
                ]
            },
            '7': {
                kpis: {
                    totalStudents: { value: 0, trend: 100, direction: 'down' },
                    revenue: { value: 0, trend: 100, direction: 'down' },
                    completionRate: { value: 82, trend: 4, direction: 'up' },
                    retentionRate: { value: 88, trend: 6, direction: 'up' },
                    watchTime: { value: 0, trend: 100, direction: 'down' },
                    quizAvg: { value: 0, trend: 100, direction: 'down' }
                },
                enrollmentTrends: [
                    { label: 'Mon', count: 0 },
                    { label: 'Tue', count: 0 },
                    { label: 'Wed', count: 0 },
                    { label: 'Thu', count: 0 },
                    { label: 'Fri', count: 0 },
                    { label: 'Sat', count: 0 },
                    { label: 'Sun', count: 0 }
                ],
                revenueTrends: [
                    { label: 'Mon', amount: 0 },
                    { label: 'Tue', amount: 0 },
                    { label: 'Wed', amount: 0 },
                    { label: 'Thu', amount: 0 },
                    { label: 'Fri', amount: 0 },
                    { label: 'Sat', amount: 0 },
                    { label: 'Sun', amount: 0 }
                ],
                completion: { completed: 0, inProgress: 0 },
                retention: [
                    { week: 'Day 1', pct: 0 },
                    { week: 'Day 2', pct: 0 },
                    { week: 'Day 3', pct: 0 },
                    { week: 'Day 5', pct: 0 },
                    { week: 'Day 7', pct: 0 }
                ],
                watchTimeByCourse: [
                    { course: 'Python for Data Science', hours: 0 },
                    { course: 'Machine Learning A-Z', hours: 0 },
                    { course: 'Deep Learning Specialization', hours: 0 },
                    { course: 'Data Engineering Essentials', hours: 0 }
                ],
                quizPerformance: [
                    { course: 'Python for Data Science', avg: 0 },
                    { course: 'Machine Learning A-Z', avg: 0 },
                    { course: 'Deep Learning Specialization', avg: 0 },
                    { course: 'Data Engineering Essentials', avg: 0 }
                ],
                geoDistribution: [
                    { country: 'No Data', flag: '📊', pct: 100 }
                ]
            },
            '30': {
                kpis: {
                    totalStudents: { value: 45, trend: 10, direction: 'down' },
                    revenue: { value: 3200, trend: 5, direction: 'down' },
                    completionRate: { value: 78, trend: 5, direction: 'up' },
                    retentionRate: { value: 85, trend: 3, direction: 'up' },
                    watchTime: { value: 15400, trend: 8, direction: 'up' },
                    quizAvg: { value: 84, trend: 2, direction: 'up' }
                },
                enrollmentTrends: [
                    { label: 'Week 1', count: 15 },
                    { label: 'Week 2', count: 12 },
                    { label: 'Week 3', count: 10 },
                    { label: 'Week 4', count: 8 }
                ],
                revenueTrends: [
                    { label: 'Week 1', amount: 900 },
                    { label: 'Week 2', amount: 850 },
                    { label: 'Week 3', amount: 780 },
                    { label: 'Week 4', amount: 670 }
                ],
                completion: { completed: 32, inProgress: 13 },
                retention: [
                    { week: 'W1', pct: 100 },
                    { week: 'W2', pct: 90 },
                    { week: 'W3', pct: 85 },
                    { week: 'W4', pct: 80 }
                ],
                watchTimeByCourse: [
                    { course: 'Python for Data Science', hours: 4800 },
                    { course: 'Machine Learning A-Z', hours: 3200 },
                    { course: 'Deep Learning Specialization', hours: 2600 },
                    { course: 'Data Engineering Essentials', hours: 1800 }
                ],
                quizPerformance: [
                    { course: 'Python for Data Science', avg: 87 },
                    { course: 'Machine Learning A-Z', avg: 83 },
                    { course: 'Deep Learning Specialization', avg: 89 },
                    { course: 'Data Engineering Essentials', avg: 80 }
                ],
                geoDistribution: [
                    { country: 'United States', flag: '🇺🇸', pct: 44 },
                    { country: 'India', flag: '🇮🇳', pct: 19 },
                    { country: 'United Kingdom', flag: '🇬🇧', pct: 12 },
                    { country: 'Germany', flag: '🇩🇪', pct: 8 },
                    { country: 'Canada', flag: '🇨🇦', pct: 6 },
                    { country: 'Australia', flag: '🇦🇺', pct: 5 },
                    { country: 'France', flag: '🇫🇷', pct: 3 },
                    { country: 'Others', flag: '🌍', pct: 3 }
                ]
            },
            '90': {
                kpis: {
                    totalStudents: { value: 1890, trend: 14, direction: 'up' },
                    revenue: { value: 21800, trend: 16, direction: 'up' },
                    completionRate: { value: 76, trend: 3, direction: 'down' },
                    retentionRate: { value: 83, trend: 4, direction: 'up' },
                    watchTime: { value: 28600, trend: 9, direction: 'up' },
                    quizAvg: { value: 83, trend: 1, direction: 'down' }
                },
                enrollmentTrends: [
                    { label: 'W1-2', count: 590 },
                    { label: 'W3-4', count: 635 },
                    { label: 'W5-6', count: 680 },
                    { label: 'W7-8', count: 720 },
                    { label: 'W9-10', count: 760 },
                    { label: 'W11-13', count: 810 }
                ],
                revenueTrends: [
                    { label: 'W1-2', amount: 5500 },
                    { label: 'W3-4', amount: 5900 },
                    { label: 'W5-6', amount: 6400 },
                    { label: 'W7-8', amount: 6800 },
                    { label: 'W9-10', amount: 7200 },
                    { label: 'W11-13', amount: 7600 }
                ],
                completion: { completed: 1436, inProgress: 454 },
                retention: [
                    { week: 'W1', pct: 100 },
                    { week: 'W2', pct: 93 },
                    { week: 'W4', pct: 85 },
                    { week: 'W8', pct: 72 },
                    { week: 'W12', pct: 62 }
                ],
                watchTimeByCourse: [
                    { course: 'Python for Data Science', hours: 8600 },
                    { course: 'Machine Learning A-Z', hours: 5600 },
                    { course: 'Deep Learning Specialization', hours: 4700 },
                    { course: 'Data Engineering Essentials', hours: 3100 }
                ],
                quizPerformance: [
                    { course: 'Python for Data Science', avg: 86 },
                    { course: 'Machine Learning A-Z', avg: 82 },
                    { course: 'Deep Learning Specialization', avg: 88 },
                    { course: 'Data Engineering Essentials', avg: 78 }
                ],
                geoDistribution: [
                    { country: 'United States', flag: '🇺🇸', pct: 45 },
                    { country: 'India', flag: '🇮🇳', pct: 18 },
                    { country: 'United Kingdom', flag: '🇬🇧', pct: 12 },
                    { country: 'Germany', flag: '🇩🇪', pct: 8 },
                    { country: 'Canada', flag: '🇨🇦', pct: 6 },
                    { country: 'Australia', flag: '🇦🇺', pct: 4 },
                    { country: 'France', flag: '🇫🇷', pct: 3 },
                    { country: 'Others', flag: '🌍', pct: 4 }
                ]
            },
            '365': {
                kpis: {
                    totalStudents: { value: 2450, trend: 12, direction: 'up' },
                    revenue: { value: 38500, trend: 18, direction: 'up' },
                    completionRate: { value: 78, trend: 5, direction: 'up' },
                    retentionRate: { value: 85, trend: 3, direction: 'up' },
                    watchTime: { value: 42000, trend: 8, direction: 'up' },
                    quizAvg: { value: 84, trend: 2, direction: 'up' }
                },
                enrollmentTrends: [
                    { label: 'Jan', count: 120 },
                    { label: 'Feb', count: 180 },
                    { label: 'Mar', count: 250 },
                    { label: 'Apr', count: 310 },
                    { label: 'May', count: 380 },
                    { label: 'Jun', count: 450 },
                    { label: 'Jul', count: 520 },
                    { label: 'Aug', count: 590 },
                    { label: 'Sep', count: 650 },
                    { label: 'Oct', count: 720 },
                    { label: 'Nov', count: 800 },
                    { label: 'Dec', count: 950 }
                ],
                revenueTrends: [
                    { label: 'Jan', amount: 2400 },
                    { label: 'Feb', amount: 3600 },
                    { label: 'Mar', amount: 5000 },
                    { label: 'Apr', amount: 6200 },
                    { label: 'May', amount: 7600 },
                    { label: 'Jun', amount: 9000 },
                    { label: 'Jul', amount: 10500 },
                    { label: 'Aug', amount: 11800 },
                    { label: 'Sep', amount: 13000 },
                    { label: 'Oct', amount: 14500 },
                    { label: 'Nov', amount: 16000 },
                    { label: 'Dec', amount: 18500 }
                ],
                completion: { completed: 1910, inProgress: 540 },
                retention: [
                    { week: 'W1', pct: 100 },
                    { week: 'W2', pct: 92 },
                    { week: 'W4', pct: 78 },
                    { week: 'W8', pct: 62 },
                    { week: 'W12', pct: 48 }
                ],
                watchTimeByCourse: [
                    { course: 'Python for Data Science', hours: 12500 },
                    { course: 'Machine Learning A-Z', hours: 8200 },
                    { course: 'Deep Learning Specialization', hours: 6800 },
                    { course: 'Data Engineering Essentials', hours: 4500 }
                ],
                quizPerformance: [
                    { course: 'Python for Data Science', avg: 86 },
                    { course: 'Machine Learning A-Z', avg: 82 },
                    { course: 'Deep Learning Specialization', avg: 88 },
                    { course: 'Data Engineering Essentials', avg: 78 }
                ],
                geoDistribution: [
                    { country: 'United States', flag: '🇺🇸', pct: 45 },
                    { country: 'India', flag: '🇮🇳', pct: 18 },
                    { country: 'United Kingdom', flag: '🇬🇧', pct: 12 },
                    { country: 'Germany', flag: '🇩🇪', pct: 8 },
                    { country: 'Canada', flag: '🇨🇦', pct: 6 },
                    { country: 'Australia', flag: '🇦🇺', pct: 4 },
                    { country: 'France', flag: '🇫🇷', pct: 3 },
                    { country: 'Others', flag: '🌍', pct: 4 }
                ]
            }
        };

        let data = analyticsData[period] || analyticsData['all'];

        // If a specific course is selected, filter the data
        if (courseFilter !== 'all') {
            data = this.filterDataByCourse(data, courseFilter);
        }

        return data;
    }

    // Filter data for a specific course
    filterDataByCourse(data, courseSlug) {
        // Find course title from slug
        const course = this.courses.find(c => c.slug === courseSlug);
        const courseTitle = course ? course.title : courseSlug;

        // Create a deep copy of the data
        const filteredData = JSON.parse(JSON.stringify(data));

        // Filter course-specific data
        if (filteredData.watchTimeByCourse) {
            filteredData.watchTimeByCourse = filteredData.watchTimeByCourse.filter(
                item => item.course === courseTitle
            );
        }

        if (filteredData.quizPerformance) {
            filteredData.quizPerformance = filteredData.quizPerformance.filter(
                item => item.course === courseTitle
            );
        }

        // Adjust KPIs for single course (in real app, backend would provide this)
        if (courseFilter !== 'all') {
            // Simulate course-specific KPI adjustments
            const adjustmentFactor = 0.25; // Single course represents ~25% of total
            filteredData.kpis.totalStudents.value = Math.round(filteredData.kpis.totalStudents.value * adjustmentFactor);
            filteredData.kpis.revenue.value = Math.round(filteredData.kpis.revenue.value * adjustmentFactor);
            filteredData.kpis.watchTime.value = Math.round(filteredData.kpis.watchTime.value * adjustmentFactor);
        }

        return filteredData;
    }

    async applyFilters() {
        // Show loading state
        this.showSkeletons();
        this.loadAnalytics()
        // ==========================================
        // REAL API CALL - Fetch new data with updated filters
        // ==========================================
        // const params = {
        //     period: this.periodFilter,
        //     course: this.courseFilter
        // };
        // this.data = await ApiService.getOverallAnalytics(params);

        // Simulate API delay


        // Re-render all charts with new data
        this.renderAll();
        this.showFilterFeedback();
    }

    renderAll() {
        this.renderKPIs();
        this.renderEnrollmentChart();
        this.renderRevenueChart();
        this.renderCompletionChart();
        this.renderWatchTimeChart();
        this.renderQuizChart();
        this.renderGeoChart();
    }

    // ============================================
    // KPI CARDS
    // ============================================
    renderKPIs() {
        const kpiData = this.data.kpis;
        const kpis = [
            { icon: '👥', key: 'totalStudents', label: 'Students', format: v => v >= 1000 ? (v/1000).toFixed(1)+'k' : v },
            { icon: '💰', key: 'revenue', label: 'Revenue', format: v => '$' + (v >= 1000 ? (v/1000).toFixed(1)+'K' : v) },
            { icon: '📊', key: 'completionRate', label: 'Completion', format: v => v + '%' },
            { icon: '⏱️', key: 'watchTime', label: 'Watch Time', format: v => v >= 1000 ? (v/1000).toFixed(1)+'kh' : v+'h' },
            { icon: '📝', key: 'quizAvg', label: 'Quiz Avg', format: v => v + '%' }
        ];

        document.getElementById('kpiGrid').innerHTML = kpis.map(k => {
            console.log("key",kpiData, k.key)
            const d = kpiData[k.key];
            return `<div class="kpi-card">
                <span class="kpi-icon">${k.icon}</span>
                <span class="kpi-value">${k.format(d.value)}</span>
                <span class="kpi-label">${k.label}</span>
                <span class="kpi-trend ${d.direction}">${d.direction === 'up' ? '↑' : d.direction === 'down' ? '↓' : '→'} ${Math.abs(d.trend)}%</span>
            </div>`;
        }).join('');
    }

    // ============================================
    // ENROLLMENT CHART (Bar)
    // ============================================
    renderEnrollmentChart() {
        const data = this.data.enrollmentTrends;
        const max = Math.max(...data.map(d => d.count));

        document.getElementById('enrollmentChartBody').innerHTML = `
            <div class="chart-placeholder">
                ${data.map(d => {
                    const h = max > 0 ? (d.count / max * 100).toFixed(0) : 0;
                    return `<div class="chart-bar-group">
                        <span class="chart-bar-value">${d.count}</span>
                        <div class="chart-bar enrollment" style="height:${h}%"></div>
                        <span class="chart-bar-label">${d.label}</span>
                    </div>`;
                }).join('')}
            </div>`;
    }

    // ============================================
    // REVENUE CHART (Bar)
    // ============================================
    renderRevenueChart() {
        const data = this.data.revenueTrends;
        const max = Math.max(...data.map(d => d.amount));

        document.getElementById('revenueChartBody').innerHTML = `
            <div class="chart-placeholder">
                ${data.map(d => {
                    const h = max > 0 ? (d.amount / max * 100).toFixed(0) : 0;
                    const formattedAmount = d.amount >= 1000
                        ? `$${(d.amount/1000).toFixed(1)}k`
                        : `$${d.amount}`;

                    return `<div class="chart-bar-group">
                        <span class="chart-bar-value">${formattedAmount}</span>
                        <div class="chart-bar revenue" style="height:${h}%"></div>
                        <span class="chart-bar-label">${d.label}</span>
                    </div>`;
                }).join('')}
            </div>`;
    }

    // ============================================
    // COMPLETION CHART (Donut)
    // ============================================
    renderCompletionChart() {
        const { completed, inProgress } = this.data.completion;
        const total = completed + inProgress;
        const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

        document.getElementById('completionChartBody').innerHTML = `
            <div class="donut-chart">
                <div class="donut-visual" style="background: conic-gradient(var(--color-success) 0deg ${pct * 3.6}deg, var(--color-primary-400) ${pct * 3.6}deg 360deg);">
                    <div class="donut-center">
                        <span class="donut-pct">${pct}%</span>
                        <span class="donut-label-sm">Completed</span>
                    </div>
                </div>
                <div class="donut-legend">
                    <div class="legend-item"><span class="legend-dot completed"></span> Completed: ${completed}</div>
                    <div class="legend-item"><span class="legend-dot progress"></span> In Progress: ${inProgress}</div>
                </div>
            </div>`;
    }

    // ============================================
    // WATCH TIME CHART (Horizontal Bars)
    // ============================================
// ============================================
// WATCH TIME CHART (Horizontal Bars)
// ============================================
renderWatchTimeChart() {
    const data = this.data.watchTimeByCourse;
    const max = Math.max(...data.map(d => d.hours));
    const colors = ['q1', 'q2', 'q3', 'q4'];

    document.getElementById('watchTimeChartBody').innerHTML = `
        <div class="hbar-list">
            ${data.map((d, i) => `
                <div class="hbar-item">
                    <span class="hbar-label">${d.course}</span>
                    <div class="hbar-track">
                        <div class="hbar-fill ${colors[i % colors.length]}" style="width:${max > 0 ? (d.hours/max*100).toFixed(0) : 0}%">
                            <span class="hbar-value">${this.formatWatchTime(d.hours)}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>`;
}

// Helper method to format watch time properly
formatWatchTime(hours) {
    if (hours >= 1000) {
        // For 1000+ hours, show in k format
        return `${(hours/1000).toFixed(1)}k h`;
    } else if (hours >= 100) {
        // For 100-999 hours, show as whole number
        return `${Math.round(hours)} h`;
    } else if (hours >= 10) {
        // For 10-99 hours, show with 1 decimal
        return `${hours.toFixed(1)} h`;
    } else if (hours >= 1) {
        // For 1-9 hours, show with 1 decimal
        return `${hours.toFixed(1)} h`;
    } else if (hours > 0) {
        // For less than 1 hour, show in minutes
        const minutes = Math.round(hours * 60);
        return `${minutes} min`;
    } else {
        // Zero hours
        return '0 h';
    }
}

    // ============================================
    // QUIZ PERFORMANCE (Horizontal Bars)
    // ============================================
    renderQuizChart() {
        const data = this.data.quizPerformance;
        const colors = ['q1', 'q2', 'q3', 'q4'];

        document.getElementById('quizChartBody').innerHTML = `
            <div class="hbar-list">
                ${data.map((d, i) => `
                    <div class="hbar-item">
                        <span class="hbar-label">${d.course}</span>
                        <div class="hbar-track">
                            <div class="hbar-fill ${colors[i % colors.length]}" style="width:${d.avg}%">
                                <span class="hbar-value">${d.avg}%</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>`;
    }

    // ============================================
    // GEOGRAPHIC DISTRIBUTION
    // ============================================
    renderGeoChart() {
        const data = this.data.geoDistribution;

        document.getElementById('geoChartBody').innerHTML = `
            <div class="geo-list">
                ${data.map(d => `
                    <div class="geo-item">
                        <span class="geo-flag">${d.flag}</span>
                        <div class="geo-info">
                            <div class="geo-country">${d.country}</div>
                            <div class="geo-pct">${d.pct}%</div>
                        </div>
                        <div class="geo-bar-mini"><div class="geo-bar-mini-fill" style="width:${d.pct}%"></div></div>
                    </div>
                `).join('')}
            </div>`;
    }

    // ============================================
    // EXPORT
    // ============================================
    exportCSV() {
        if (!this.data) {
            this.showToast('No data to export');
            return;
        }

        // Build CSV content from the current analytics data
        const csvRows = [];

        // Add header row
        csvRows.push('Analytics Export');
        csvRows.push(`Period: ${this.periodFilter}`);
        csvRows.push(`Course: ${this.courseFilter}`);
        csvRows.push('');

        // KPIs section
        csvRows.push('KPIs');
        csvRows.push('Metric,Value,Trend,Direction');
        const kpis = this.data.kpis;
        csvRows.push(`Total Students,${kpis.totalStudents.value},${kpis.totalStudents.trend}%,${kpis.totalStudents.direction}`);
        csvRows.push(`Revenue,${kpis.revenue.value},${kpis.revenue.trend}%,${kpis.revenue.direction}`);
        csvRows.push(`Completion Rate,${kpis.completionRate.value}%,${kpis.completionRate.trend}%,${kpis.completionRate.direction}`);
        csvRows.push(`Watch Time,${kpis.watchTime.value},${kpis.watchTime.trend}%,${kpis.watchTime.direction}`);
        csvRows.push(`Quiz Average,${kpis.quizAvg.value}%,${kpis.quizAvg.trend}%,${kpis.quizAvg.direction}`);
        csvRows.push('');

        // Enrollment Trends
        csvRows.push('Enrollment Trends');
        csvRows.push('Period,Enrollments');
        this.data.enrollmentTrends.forEach(item => {
            csvRows.push(`${item.label},${item.count}`);
        });
        csvRows.push('');

        // Revenue Trends
        csvRows.push('Revenue Trends');
        csvRows.push('Period,Revenue');
        this.data.revenueTrends.forEach(item => {
            csvRows.push(`${item.label},${item.amount}`);
        });
        csvRows.push('');

        // Completion
        csvRows.push('Completion');
        csvRows.push('Status,Count');
        csvRows.push(`Completed,${this.data.completion.completed}`);
        csvRows.push(`In Progress,${this.data.completion.inProgress}`);
        csvRows.push('');



        // Watch Time by Course
        csvRows.push('Watch Time by Course');
        csvRows.push('Course,Hours');
        this.data.watchTimeByCourse.forEach(item => {
            csvRows.push(`${item.course},${item.hours}`);
        });
        csvRows.push('');

        // Quiz Performance
        csvRows.push('Quiz Performance');
        csvRows.push('Course,Average Score');
        this.data.quizPerformance.forEach(item => {
            csvRows.push(`${item.course},${item.avg}%`);
        });
        csvRows.push('');

        // Geographic Distribution
        csvRows.push('Geographic Distribution');
        csvRows.push('Country,Percentage');
        this.data.geoDistribution.forEach(item => {
            csvRows.push(`${item.country},${item.pct}%`);
        });

        // Convert to CSV string
        const csvContent = csvRows.join('\n');

        // Create and download the CSV file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `analytics_${this.periodFilter}_${this.courseFilter}_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);

        this.showToast('Analytics exported to CSV');
    }

    showFilterFeedback() {
        const periodLabel = document.getElementById('periodFilter')?.options[document.getElementById('periodFilter')?.selectedIndex]?.text;
        const courseLabel = document.getElementById('courseFilter')?.options[document.getElementById('courseFilter')?.selectedIndex]?.text;

        if (periodLabel && courseLabel) {
            console.log(`Showing data for: ${periodLabel} - ${courseLabel}`);
            // Optional: Show a toast notification
            // this.showToast(`Showing ${periodLabel} data for ${courseLabel}`);
        }
    }

    showSkeletons() {
        document.getElementById('kpiGrid').innerHTML = Array(6).fill('<div class="kpi-card"><div class="skeleton-block" style="height:60px;"></div></div>').join('');
        document.querySelectorAll('.chart-body').forEach(el => el.innerHTML = '<div class="skeleton-block" style="height:200px;"></div>');
    }

    hideLoader() {
        document.getElementById('loadingOverlay')?.classList.add('hidden');
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
}

let instructorAnalyticsPage;
document.addEventListener('DOMContentLoaded', () => {
    instructorAnalyticsPage = new InstructorAnalyticsPage();
});
