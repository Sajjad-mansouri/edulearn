// ============================================
// INSTRUCTOR STUDENTS PAGE CONTROLLER
// ============================================

class InstructorStudentsPage {
    constructor() {
        this.searchQuery = '';
        this.courseFilter = 'all';
        this.statusFilter = 'all';
        this.sortBy = 'name-asc';
        this.currentPage = 1;
        this.perPage = 10;
        this.allStudents = [];
        this.filteredStudents = [];
        this.selectedStudents = new Set();
        this.messageRecipients = [];
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadStudents();
        this.loadCourses()
        this.hideLoader();
    }

    bindEvents() {

        // Search
        const si = document.getElementById('studentSearch');
        const sc = document.getElementById('searchClearBtn');
        si?.addEventListener('input', (e) => { this.searchQuery = e.target.value.toLowerCase().trim(); sc.style.display = this.searchQuery ? 'flex' : 'none'; this.applyFilters(); });
        sc?.addEventListener('click', () => { si.value = ''; this.searchQuery = ''; sc.style.display = 'none'; this.applyFilters(); });

        // Filters
        document.getElementById('courseFilter')?.addEventListener('change', (e) => { this.courseFilter = e.target.value; this.applyFilters(); });
        document.getElementById('statusFilter')?.addEventListener('change', (e) => { this.statusFilter = e.target.value; this.applyFilters(); });
        document.getElementById('sortSelect')?.addEventListener('change', (e) => { this.sortBy = e.target.value; this.applyFilters(); });

        // Select All
        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));
        document.getElementById('headerCheckbox')?.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));

        // Bulk actions
        document.getElementById('messageSelectedBtn')?.addEventListener('click', () => this.openMessageModal([...this.selectedStudents]));
        document.getElementById('exportBtn')?.addEventListener('click', () => this.exportCSV());

        // Modals
        document.getElementById('detailModalClose')?.addEventListener('click', () => document.getElementById('studentDetailModal').style.display = 'none');
        document.getElementById('studentDetailModal')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) document.getElementById('studentDetailModal').style.display = 'none'; });
        document.getElementById('messageModalClose')?.addEventListener('click', () => document.getElementById('messageModal').style.display = 'none');
        document.getElementById('messageModalCancel')?.addEventListener('click', () => document.getElementById('messageModal').style.display = 'none');
        document.getElementById('messageModal')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) document.getElementById('messageModal').style.display = 'none'; });
        document.getElementById('sendMessageBtn')?.addEventListener('click', () => this.sendMessage());

        // Pagination
        document.getElementById('prevPage')?.addEventListener('click', () => this.changePage(-1));
        document.getElementById('nextPage')?.addEventListener('click', () => this.changePage(1));
    }

    // ============================================
    // DATA LOADING
    // ============================================
    mapData(allStudents) {
        const payloads = [];
        allStudents.forEach(student => {
            const { enrolled_courses, overall_progress, last_active, ...rest } = student;
            const payload = {
                ...rest,
                enrolledCourses:  enrolled_courses,
                overallProgress: overall_progress,
                lastActive:last_active
            };
            payloads.push(payload);
        });
        return payloads;
    }
    async loadStudents() {
        this.showSkeletons();

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/students/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load students.");
            }

            const data = await response.json();
            this.allStudents = this.mapData(data.students ?? []);
            this.avgRating = data.statistics.average_course_rating
            this.instructorCourses = data.statistics.courses



        } catch (error) {
            this.allStudents = []
            console.error("Error loading students:", error);
        }

        this.applyFilters();
    }

    loadCourses(){
        const select = document.getElementById("courseFilter");

        // Keep the default "All Courses" option
        select.innerHTML = '<option value="all">All Courses</option>';

        Object.entries(this.instructorCourses).forEach(([slug, title]) => {
          const option = document.createElement("option");
          option.value = slug;
          option.textContent = title;
          select.appendChild(option);
});
    }

    getDummyStudents() {

        const courses = ['Python for Data Science', 'Machine Learning A-Z', 'Deep Learning Specialization', 'Data Engineering Essentials', 'SQL for Data Analysis'];
        const statuses = ['active', 'active', 'active', 'idle', 'idle', 'stalled', 'completed', 'completed'];
        const names = [
            'Jane Smith', 'Mike Lee', 'Anna Kim', 'Tom Brown', 'Lisa Wang',
            'David Park', 'Emma Wilson', 'Carlos Mendez', 'Priya Sharma', 'James Taylor',
            'Sophie Martin', 'Alex Johnson', 'Maria Garcia', 'Ryan O\'Neal', 'Yuki Tanaka',
            'Oliver Chen', 'Fatima Ali', 'Nina Petrova', 'Sam Wilson', 'Zara Khan'
        ];

        return names.map((name, i) => {
            const enrolled = [courses[i % courses.length]];
            if (i % 3 === 0) enrolled.push(courses[(i + 1) % courses.length]);
            const progress = Math.floor(Math.random() * 100) + 1;
            const status = progress === 100 ? 'completed' : statuses[i % statuses.length];
            const daysAgo = status === 'active' ? Math.floor(Math.random() * 7) : status === 'idle' ? Math.floor(Math.random() * 23) + 7 : status === 'stalled' ? Math.floor(Math.random() * 60) + 30 : Math.floor(Math.random() * 14);

            return {
                id: i + 1,
                name,
                email: name.toLowerCase().replace(/ /g, '.') + '@email.com',
                avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${['4F46E5','8B5CF6','10B981','F59E0B','EC4899','3B82F6'][i%6]}&color=fff&size=76`,
                enrolledCourses: enrolled.map(c => ({
                    name: c,
                    progress: Math.floor(Math.random() * 100) + 1
                })),
                overallProgress: progress,
                status,
                lastActive: new Date(Date.now() - daysAgo * 86400000)
            };
        });
    }

    // ============================================
    // FILTERING
    // ============================================
    applyFilters() {
        let students = [...this.allStudents];

        if (this.searchQuery) {
            students = students.filter(s => s.name.toLowerCase().includes(this.searchQuery) || s.email.toLowerCase().includes(this.searchQuery));
        }
        if (this.courseFilter !== 'all') {
            students = students.filter(s => s.enrolledCourses.some(c => c.name.toLowerCase().replace(/ /g, '-') === this.courseFilter || c.name === this._getCourseName(this.courseFilter)));
        }
        if (this.statusFilter !== 'all') {
            students = students.filter(s => s.status === this.statusFilter);
        }

        students = this.sortStudents(students);
        this.filteredStudents = students;
        this.selectedStudents.clear();
        this.currentPage = 1;
        this.renderAll();
    }

    _getCourseName(slug) {
        const map = this.instructorCourses;
        return map[slug] || slug;
    }

    sortStudents(students) {
        switch(this.sortBy) {
            case 'name-asc': return students.sort((a,b) => a.name.localeCompare(b.name));
            case 'name-desc': return students.sort((a,b) => b.name.localeCompare(a.name));
            case 'progress-desc': return students.sort((a,b) => b.overallProgress - a.overallProgress);
            case 'progress-asc': return students.sort((a,b) => a.overallProgress - b.overallProgress);
            case 'recent': return students.sort((a,b) => b.lastActive - a.lastActive);
            case 'oldest': return students.sort((a,b) => a.lastActive - b.lastActive);
            default: return students;
        }
    }

    // ============================================
    // RENDER ALL
    // ============================================
    renderAll() {
        this.renderStatistics();
        this.renderResultsInfo();
        this.renderStudentTable();
        this.renderStudentCards();
        this.renderPagination();
        this.updateBulkBar();
        this.checkEmptyState();
    }

    renderStatistics() {
        const total = this.allStudents.length;
        const active = this.allStudents.filter(s => s.status === 'active').length;
        const avgProgress = total > 0 ? Math.round(this.allStudents.reduce((s, st) => s + st.overallProgress, 0) / total) : 0;
        const avgRating = this.avgRating;
        document.getElementById('statTotal').textContent = this.formatNum(total);
        document.getElementById('statActive').textContent = this.formatNum(active);
        document.getElementById('statCompletion').textContent = `${avgProgress}%`;
        document.getElementById('statRating').textContent = avgRating;
    }

    renderResultsInfo() {
        document.getElementById('showingCount').textContent = this.filteredStudents.length;
    }

    renderStudentTable() {
        const tbody = document.getElementById('studentTableBody');
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredStudents.slice(start, start + this.perPage);

        tbody.innerHTML = page.map(s => `
            <tr>
                <td class="col-check"><input type="checkbox" class="student-checkbox" data-id="${s.id}"></td>
                <td class="col-student">
                    <div class="student-info-cell">
                        <img src="${s.avatar}" alt="${s.name}" class="student-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(s.name)}&background=6B7280&color=fff&size=76'">
                        <div class="student-name-email">
                            <span class="student-name" onclick="instructorStudentsPage.viewStudent(${s.id})">${s.name}</span>
                            <span class="student-email">${s.email}</span>
                        </div>
                    </div>
                </td>
                <td class="col-courses">
                    <div class="courses-cell">
                        ${s.enrolledCourses.map(c => `
                            <div class="course-chip">
                                <span>${c.name}</span>
                                <div class="mini-bar"><div class="mini-bar-fill" style="width:${c.progress}%"></div></div>
                                <span class="chip-pct">${c.progress}%</span>
                            </div>
                        `).join('')}
                    </div>
                </td>
                <td class="col-progress">
                    <div class="progress-cell">
                        <div class="progress-bar-sm"><div class="progress-bar-sm-fill ${s.overallProgress >= 80 ? 'high' : s.overallProgress >= 40 ? 'medium' : 'low'}" style="width:${s.overallProgress}%"></div></div>
                        <span class="progress-pct">${s.overallProgress}%</span>
                    </div>
                </td>
                <td class="col-status">
                    <span class="status-badge-sm ${s.status}"><span class="status-dot ${s.status}"></span> ${this.capitalize(s.status)}</span>
                </td>
                <td class="col-last-active"><span class="last-active-cell">${this.formatRelative(s.lastActive)}</span></td>
                <td class="col-actions">
                    <div class="actions-cell">
                        <button class="student-action-btn view" title="View details" onclick="instructorStudentsPage.viewStudent(${s.id})"><i class="fas fa-eye"></i></button>
                        <button class="student-action-btn message" title="Send message" onclick="instructorStudentsPage.openMessageModal([${s.id}])"><i class="fas fa-envelope"></i></button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Bind checkbox events
        tbody.querySelectorAll('.student-checkbox').forEach(cb => {
            cb.addEventListener('change', () => {
                const id = parseInt(cb.dataset.id);
                cb.checked ? this.selectedStudents.add(id) : this.selectedStudents.delete(id);
                this.updateBulkBar();
            });
        });
    }

    renderStudentCards() {
        const container = document.getElementById('studentCardsList');
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredStudents.slice(start, start + this.perPage);

        container.innerHTML = page.map(s => `
            <div class="student-card">
                <div class="student-card-top">
                    <input type="checkbox" class="student-checkbox" data-id="${s.id}" style="margin-top:4px;">
                    <img src="${s.avatar}" alt="${s.name}" class="student-card-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(s.name)}&background=6B7280&color=fff&size=88'">
                    <div class="student-card-info">
                        <div class="student-card-name">${s.name}</div>
                        <div class="student-card-email">${s.email}</div>
                        <span class="status-badge-sm ${s.status}" style="margin-top:4px;"><span class="status-dot ${s.status}"></span> ${this.capitalize(s.status)}</span>
                    </div>
                </div>
                <div class="student-card-courses">
                    ${s.enrolledCourses.map(c => `<span class="student-card-course-tag">${c.name} (${c.progress}%)</span>`).join('')}
                </div>
                <div class="student-card-footer">
                    <div class="student-card-progress">
                        <div class="progress-bar-sm" style="width:80px;"><div class="progress-bar-sm-fill ${s.overallProgress >= 80 ? 'high' : s.overallProgress >= 40 ? 'medium' : 'low'}" style="width:${s.overallProgress}%"></div></div>
                        <span class="progress-pct">${s.overallProgress}%</span>
                    </div>
                    <div class="student-card-actions">
                        <button class="student-action-btn view" onclick="instructorStudentsPage.viewStudent(${s.id})"><i class="fas fa-eye"></i></button>
                        <button class="student-action-btn message" onclick="instructorStudentsPage.openMessageModal([${s.id}])"><i class="fas fa-envelope"></i></button>
                    </div>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.student-checkbox').forEach(cb => {
            cb.addEventListener('change', () => {
                const id = parseInt(cb.dataset.id);
                cb.checked ? this.selectedStudents.add(id) : this.selectedStudents.delete(id);
                this.updateBulkBar();
            });
        });
    }

    // ============================================
    // SELECTION & BULK
    // ============================================
    toggleSelectAll(checked) {
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredStudents.slice(start, start + this.perPage);
        page.forEach(s => checked ? this.selectedStudents.add(s.id) : this.selectedStudents.delete(s.id));
        document.querySelectorAll('.student-checkbox').forEach(cb => { cb.checked = checked; });
        document.getElementById('headerCheckbox').checked = checked;
        document.getElementById('selectAllCheckbox').checked = checked;
        this.updateBulkBar();
    }

    updateBulkBar() {
        const count = this.selectedStudents.size;
        document.getElementById('bulkSelectedCount').textContent = `${count} selected`;
        document.getElementById('messageSelectedBtn').disabled = count === 0;
        document.getElementById('exportBtn').disabled = count === 0;
    }

    exportCSV() {
        const students = this.allStudents.filter(s => this.selectedStudents.has(s.id));
        if (students.length === 0) { this.showToast('No students selected'); return; }
        const headers = ['Name', 'Email', 'Enrolled Courses', 'Progress', 'Status', 'Last Active'];
        const rows = students.map(s => [s.name, s.email, s.enrolledCourses.map(c=>c.name).join('; '), `${s.overallProgress}%`, s.status, this.formatDate(s.lastActive)]);
        const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'students.csv'; a.click();
        URL.revokeObjectURL(url);
        this.showToast('CSV exported');
    }

    // ============================================
    // STUDENT DETAIL MODAL
    // ============================================
    viewStudent(id) {
        const student = this.allStudents.find(s => s.id === id);
        if (!student) return;

        document.getElementById('detailModalTitle').textContent = student.name;
        document.getElementById('detailModalBody').innerHTML = `
            <div class="detail-student-header">
                <img src="${student.avatar}" alt="${student.name}" class="detail-avatar">
                <div>
                    <div class="detail-name">${student.name}</div>
                    <div class="detail-email">${student.email}</div>
                    <span class="status-badge-sm ${student.status}" style="margin-top:4px;"><span class="status-dot ${student.status}"></span> ${this.capitalize(student.status)}</span>
                </div>
            </div>
            <div class="detail-section">
                <h4>Enrolled Courses</h4>
                ${student.enrolledCourses.map(c => `
                    <div class="detail-course-row">
                        <span class="detail-course-name">${c.name}</span>
                        <span class="detail-course-progress">${c.progress}%</span>
                    </div>
                `).join('')}
            </div>
            <div class="detail-section">
                <h4>Activity</h4>
                <p style="font-size:0.85rem;color:var(--color-gray-500);">Last active: ${this.formatRelative(student.lastActive)}</p>
            </div>
        `;
        document.getElementById('studentDetailModal').style.display = 'flex';
    }

    // ============================================
    // MESSAGE MODAL
    // ============================================
    openMessageModal(studentIds) {
        this.messageRecipients = studentIds;
        const names = studentIds.map(id => this.allStudents.find(s => s.id === id)?.name || `Student #${id}`);
        document.getElementById('messageRecipients').value = names.join(', ');
        document.getElementById('messageSubject').value = '';
        document.getElementById('messageBody').value = '';
        document.getElementById('messageModal').style.display = 'flex';
    }

    sendMessage() {
        const subject = document.getElementById('messageSubject').value.trim();
        const body = document.getElementById('messageBody').value.trim();
        if (!subject || !body) { this.showToast('Please fill in subject and message'); return; }

        // ==========================================
        // REAL API CALL
        // ==========================================
        // await ApiService.post('/instructor/students/message/', {
        //     recipients: this.messageRecipients,
        //     subject,
        //     message: body
        // });

        document.getElementById('messageModal').style.display = 'none';
        this.showToast(`Message sent to ${this.messageRecipients.length} student(s)`);
        this.messageRecipients = [];
    }

    // ============================================
    // PAGINATION
    // ============================================
    renderPagination() {
        const total = Math.ceil(this.filteredStudents.length / this.perPage);
        const c = document.getElementById('pageNumbers');
        if (total <= 1) { c.innerHTML = ''; document.getElementById('prevPage').disabled = true; document.getElementById('nextPage').disabled = true; return; }
        document.getElementById('prevPage').disabled = this.currentPage <= 1;
        document.getElementById('nextPage').disabled = this.currentPage >= total;
        c.innerHTML = Array.from({length: total}, (_, i) => `<button class="page-number ${i+1===this.currentPage?'active':''}" data-page="${i+1}">${i+1}</button>`).join('');
        c.querySelectorAll('.page-number').forEach(b => b.addEventListener('click', () => { this.currentPage = parseInt(b.dataset.page); this.renderStudentTable(); this.renderStudentCards(); this.renderPagination(); }));
    }

    changePage(d) {
        const total = Math.ceil(this.filteredStudents.length / this.perPage);
        const np = this.currentPage + d;
        if (np >= 1 && np <= total) { this.currentPage = np; this.renderStudentTable(); this.renderStudentCards(); this.renderPagination(); }
    }

    checkEmptyState() {
        const show = this.filteredStudents.length === 0;
        document.getElementById('studentTableBody').style.display = show ? 'none' : '';
        document.getElementById('studentCardsList').style.display = show ? 'none' : '';
        document.getElementById('pagination').style.display = show ? 'none' : '';
        document.getElementById('emptyState').style.display = show ? 'block' : 'none';
        document.getElementById('resultsInfo').style.display = show ? 'none' : '';
        document.getElementById('bulkActionsBar').style.display = show ? 'none' : '';
    }

    showSkeletons() {
        document.getElementById('studentTableBody').innerHTML = Array(8).fill('<tr><td colspan="7"><div class="skeleton-line" style="height:50px;"></div></td></tr>').join('');
    }

    hideLoader() { document.getElementById('loadingOverlay')?.classList.add('hidden'); }

    // Utilities
    formatNum(n) { return n >= 1000 ? (n/1000).toFixed(1)+'k' : n.toString(); }
    capitalize(s) { return s ? s.charAt(0).toUpperCase()+s.slice(1) : ''; }
    formatDate(d) { return d.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }); }
formatRelative(d) {
    if (!d) return '';

    const time = typeof d === 'string'
        ? new Date(d).getTime()
        : d;

    const diff = Math.floor((Date.now() - time) / 86400000);

    if (diff === 0) return 'Today';
    if (diff === 1) return 'Yesterday';
    if (diff < 7) return `${diff}d ago`;
    if (diff < 30) return `${Math.floor(diff / 7)}w ago`;
    return `${Math.floor(diff / 30)}mo ago`;
}    showToast(m) { const t=document.createElement('div'); t.className='toast-popup'; t.textContent=m; document.getElementById('toastContainer').appendChild(t); requestAnimationFrame(()=>{t.style.opacity='1';t.style.transform='translateY(0)';}); setTimeout(()=>{t.style.opacity='0';setTimeout(()=>t.remove(),300);},3000); }
}

let instructorStudentsPage;
document.addEventListener('DOMContentLoaded', () => { instructorStudentsPage = new InstructorStudentsPage(); });
