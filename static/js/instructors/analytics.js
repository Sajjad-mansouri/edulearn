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


            this.data = data



        } catch (error) {
            this.data = {}
            console.error("Error loading analytics:", error);
        }

        this.renderAll();
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
