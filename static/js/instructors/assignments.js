// ============================================
// INSTRUCTOR ASSIGNMENTS PAGE CONTROLLER
// ============================================


class InstructorAssignmentsPage {
    constructor() {
        this.searchQuery = '';
        this.courseFilter = 'all';
        this.assignmentFilter = 'all';
        this.statusFilter = 'all';
        this.sortBy = 'newest';
        this.currentPage = 1;
        this.perPage = 10;
        this.allSubmissions = [];
        this.filteredSubmissions = [];
        this.selectedSubmissions = new Set();
        this.currentGradeId = null;
        this.currentViewSubmissionId = null;
        this.init();
    }

    async init() {
        this.ensureModalsExist();
        this.bindEvents();
        await this.populateCourseOptions()
        await this.loadSubmissions();
        this.hideLoader();
    }

    ensureModalsExist() {
        if (!document.getElementById('toastContainer')) {
            const toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        if (!document.getElementById('viewSubmissionModal')) {
            const viewModal = document.createElement('div');
            viewModal.id = 'viewSubmissionModal';
            viewModal.className = 'modal-overlay';
            viewModal.style.display = 'none';
            viewModal.innerHTML = `
                <div class="modal-container modal-lg">
                    <div class="modal-header">
                        <h3 id="viewModalTitle">Submission Details</h3>
                        <button class="modal-close view-modal-close-btn">&times;</button>
                    </div>
                    <div class="modal-body" id="viewModalBody"></div>
                    <div class="modal-footer">
                        <button class="nav-btn secondary view-modal-cancel-btn">Close</button>
                    </div>
                </div>
            `;
            document.body.appendChild(viewModal);

            viewModal.addEventListener('click', (e) => {
                if (e.target === viewModal) {
                    viewModal.style.display = 'none';
                }
            });

            const viewCloseBtn = viewModal.querySelector('.view-modal-close-btn');
            const viewCancelBtn = viewModal.querySelector('.view-modal-cancel-btn');

            if (viewCloseBtn) {
                viewCloseBtn.addEventListener('click', () => {
                    viewModal.style.display = 'none';
                });
            }
            if (viewCancelBtn) {
                viewCancelBtn.addEventListener('click', () => {
                    viewModal.style.display = 'none';
                });
            }
        }

        if (!document.getElementById('fileViewerModal')) {
            const fileViewerModal = document.createElement('div');
            fileViewerModal.id = 'fileViewerModal';
            fileViewerModal.className = 'modal-overlay';
            fileViewerModal.style.display = 'none';
            fileViewerModal.innerHTML = `
                <div class="modal-container modal-lg">
                    <div class="modal-header">
                        <h3 id="fileViewerTitle">File Preview</h3>
                        <button class="modal-close file-viewer-close-btn">&times;</button>
                    </div>
                    <div class="modal-body" id="fileViewerBody"></div>
                    <div class="modal-footer">
                        <button class="nav-btn primary" id="fileViewerDownloadBtn">
                            <i class="fas fa-download"></i> Download File
                        </button>
                        <button class="nav-btn secondary file-viewer-cancel-btn">Close</button>
                    </div>
                </div>
            `;
            document.body.appendChild(fileViewerModal);

            fileViewerModal.addEventListener('click', (e) => {
                if (e.target === fileViewerModal) {
                    fileViewerModal.style.display = 'none';
                }
            });

            const fileViewerCloseBtn = fileViewerModal.querySelector('.file-viewer-close-btn');
            const fileViewerCancelBtn = fileViewerModal.querySelector('.file-viewer-cancel-btn');

            if (fileViewerCloseBtn) {
                fileViewerCloseBtn.addEventListener('click', () => {
                    fileViewerModal.style.display = 'none';
                });
            }
            if (fileViewerCancelBtn) {
                fileViewerCancelBtn.addEventListener('click', () => {
                    fileViewerModal.style.display = 'none';
                });
            }
        }
    }

    bindEvents() {

        const si = document.getElementById('assignSearch');
        const sc = document.getElementById('searchClearBtn');
        si?.addEventListener('input', (e) => { this.searchQuery = e.target.value.toLowerCase().trim(); sc.style.display = this.searchQuery ? 'flex' : 'none'; this.applyFilters(); });
        sc?.addEventListener('click', () => { si.value = ''; this.searchQuery = ''; sc.style.display = 'none'; this.applyFilters(); });

        document.getElementById('courseFilter')?.addEventListener('change', (e) => { this.courseFilter = e.target.value; this.applyFilters(); });
        document.getElementById('assignmentFilter')?.addEventListener('change', (e) => { this.assignmentFilter = e.target.value; this.applyFilters(); });
        document.getElementById('statusFilter')?.addEventListener('change', (e) => { this.statusFilter = e.target.value; this.applyFilters(); });
        document.getElementById('sortSelect')?.addEventListener('change', (e) => { this.sortBy = e.target.value; this.applyFilters(); });

        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));
        document.getElementById('headerCheckbox')?.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));

        document.getElementById('bulkDownloadBtn')?.addEventListener('click', () => this.bulkDownload());

        const gradeModal = document.getElementById('gradeModal');
        const gradeModalClose = document.getElementById('gradeModalClose');
        const gradeModalCancel = document.getElementById('gradeModalCancel');
        const submitGradeBtn = document.getElementById('submitGradeBtn');

        if (gradeModalClose) {
            gradeModalClose.addEventListener('click', () => {
                if (gradeModal) gradeModal.style.display = 'none';
            });
        }
        if (gradeModalCancel) {
            gradeModalCancel.addEventListener('click', () => {
                if (gradeModal) gradeModal.style.display = 'none';
            });
        }
        if (gradeModal) {
            gradeModal.addEventListener('click', (e) => {
                if (e.target === gradeModal) gradeModal.style.display = 'none';
            });
        }
        if (submitGradeBtn) {
            submitGradeBtn.addEventListener('click', () => this.submitGrade());
        }

        const viewSubmissionModal = document.getElementById('viewSubmissionModal');
        const viewModalClose = document.getElementById('viewModalClose');
        const viewModalCancel = document.getElementById('viewModalCancel');

        if (viewModalClose && viewSubmissionModal) {
            viewModalClose.addEventListener('click', () => {
                viewSubmissionModal.style.display = 'none';
            });
        }
        if (viewModalCancel && viewSubmissionModal) {
            viewModalCancel.addEventListener('click', () => {
                viewSubmissionModal.style.display = 'none';
            });
        }
        if (viewSubmissionModal) {
            viewSubmissionModal.addEventListener('click', (e) => {
                if (e.target === viewSubmissionModal) {
                    viewSubmissionModal.style.display = 'none';
                }
            });
        }

        const fileViewerModal = document.getElementById('fileViewerModal');
        const fileViewerClose = document.getElementById('fileViewerClose');
        const fileViewerCancel = document.getElementById('fileViewerCancel');

        if (fileViewerClose && fileViewerModal) {
            fileViewerClose.addEventListener('click', () => {
                fileViewerModal.style.display = 'none';
            });
        }
        if (fileViewerCancel && fileViewerModal) {
            fileViewerCancel.addEventListener('click', () => {
                fileViewerModal.style.display = 'none';
            });
        }
        if (fileViewerModal) {
            fileViewerModal.addEventListener('click', (e) => {
                if (e.target === fileViewerModal) {
                    fileViewerModal.style.display = 'none';
                }
            });
        }

        document.getElementById('prevPage')?.addEventListener('click', () => this.changePage(-1));
        document.getElementById('nextPage')?.addEventListener('click', () => this.changePage(1));
    }

    mapData(allAssignments) {
        const payloads = [];
        allAssignments.forEach(assignment => {
            const { student_name, student_email, student_avatar, assignment_name, assignment_desc, course_name, course_slug, letter_grade, submitted_at, graded_at, submission_text, files, ...rest } = assignment;
            const payload = {
                ...rest,
                studentName: student_name,
                studentEmail: student_email,
                studentAvatar: student_avatar,
                assignmentName: assignment_name,
                assignmentDesc: assignment_desc,
                courseName: course_name,
                courseSlug: course_slug,
                letterGrade: letter_grade,
                submitDate: new Date(submitted_at),
                gradedDate: new Date(graded_at),
                submissionText: submission_text,
                files: files || [],
            };
            payloads.push(payload);
        });
        return payloads;
    }

    async loadSubmissions() {
        this.showSkeletons();
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/assignments/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load assignments.");
            }

            const data = await response.json();
            const allSubmissions = this.mapData(data.results ?? []);
            console.log(allSubmissions)
            if (allSubmissions && allSubmissions.length > 0) {
                this.allSubmissions = allSubmissions;
            } else {
                this.allSubmissions = [];
            }

        } catch (error) {
            console.error("Error loading assignments:", error);
            this.allSubmissions = [];
        }

        this.applyFilters();
    }
    async loadInstructorCourses(){
               try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/courses/compact/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to load courses.");
            }

            const data = await response.json();

            this.instructorCourses = data.courses


        } catch (error) {
            console.error("Error loading assignments:", error);
            this.allSubmissions = [];
        }
    }
    async populateCourseOptions(){
        await this.loadInstructorCourses()
        const select = document.getElementById("courseFilter");

        // Keep the default "All Courses" option
        select.innerHTML = '<option value="all">All Courses</option>';
        console.log(this.instructorCourses)
        Object.entries(this.instructorCourses).forEach(([slug, title]) => {
          const option = document.createElement("option");
          option.value = slug;
          option.textContent = title;
          select.appendChild(option);
});
    }

    getDummySubmissions() {
        const statuses = ['pending', 'pending', 'pending', 'late', 'late', 'graded', 'graded', 'graded'];
        const students = ['Jane Smith', 'Mike Lee', 'Anna Kim', 'Tom Brown', 'Lisa Wang', 'David Park', 'Emma Wilson', 'Carlos Mendez'];
        const assignments = [
            { name: 'Assignment 4: Data Visualization', desc: 'Create interactive charts using Plotly' },
            { name: 'Quiz 3: Machine Learning Concepts', desc: 'Multiple choice and short answer' },
            { name: 'Assignment 3: Pandas Exercise', desc: 'Data cleaning and transformation' },
            { name: 'Final Project Proposal', desc: 'Project scope and methodology' },
        ];
        const courses = ['Python for Data Science', 'Machine Learning A-Z', 'Deep Learning Specialization', 'Data Engineering Essentials'];
        return Array.from({ length: 24 }, (_, i) => {
            const status = statuses[i % statuses.length];
            const assignment = assignments[i % assignments.length];
            const course = courses[i % courses.length];
            const submitDate = status === 'late' ? new Date(Date.now() - (1 + Math.floor(Math.random() * 5)) * 86400000) : new Date(Date.now() - Math.floor(Math.random() * 72) * 3600000);
            const graded = status === 'graded';
            const score = graded ? Math.floor(Math.random() * 31) + 70 : null;
            const submissionId = i + 1;
            return {
                id: submissionId,
                studentName: students[i % students.length],
                studentEmail: students[i % students.length].toLowerCase().replace(' ', '.') + '@email.com',
                studentAvatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(students[i % students.length])}&background=${['4F46E5','8B5CF6','10B981','F59E0B'][i%4]}&color=fff&size=72`,
                assignmentName: assignment.name,
                assignmentDesc: assignment.desc,
                courseName: course,
                courseSlug: course.toLowerCase().replace(/ /g, '-'),
                status,
                submitDate,
                gradedDate: graded ? new Date(submitDate.getTime() + Math.floor(Math.random() * 48) * 3600000) : null,
                score,
                letterGrade: graded ? (score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : 'D') : null,
                feedback: graded ? ['Great work!', 'Well done.', 'Good effort, keep improving.', 'Excellent analysis.'][i % 4] : '',
                submissionText: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n\nKey findings:\n- Data analysis completed\n- Visualizations included\n- Code is well-documented',
                files: this.generateDummyFiles(submissionId)
            };
        });
    }

    generateDummyFiles(submissionId) {
        const fileTypes = [
            { name: 'submission.py', type: 'python', size: '12.5 KB' },
            { name: 'analysis.ipynb', type: 'notebook', size: '245.3 KB' },
            { name: 'report.pdf', type: 'pdf', size: '1.2 MB' },
            { name: 'data.csv', type: 'csv', size: '45.8 KB' },
            { name: 'visualization.png', type: 'image', size: '320.1 KB' },
            { name: 'README.md', type: 'markdown', size: '2.1 KB' },
            { name: 'requirements.txt', type: 'text', size: '0.5 KB' },
            { name: 'main.js', type: 'javascript', size: '8.3 KB' }
        ];

        const numFiles = Math.floor(Math.random() * 4) + 1;
        const selectedFiles = [];
        const usedIndices = new Set();

        while (selectedFiles.length < numFiles) {
            const index = Math.floor(Math.random() * fileTypes.length);
            if (!usedIndices.has(index)) {
                usedIndices.add(index);
                selectedFiles.push({
                    ...fileTypes[index],
                    id: `${submissionId}-file-${index}`,
                    path: `#file-${submissionId}-${index}`,
                    uploadedAt: new Date(Date.now() - Math.floor(Math.random() * 72) * 3600000).toISOString()
                });
            }
        }

        return selectedFiles;
    }

    applyFilters() {
        let subs = [...this.allSubmissions];
        if (this.searchQuery) subs = subs.filter(s => s.studentName.toLowerCase().includes(this.searchQuery) || s.assignmentName.toLowerCase().includes(this.searchQuery) || s.courseName.toLowerCase().includes(this.searchQuery));
        if (this.courseFilter !== 'all') subs = subs.filter(s => s.courseSlug === this.courseFilter || s.courseName === this._getCourseName(this.courseFilter));
        if (this.assignmentFilter !== 'all') subs = subs.filter(s => s.assignmentName.includes(this._getAssignmentName(this.assignmentFilter)));
        if (this.statusFilter !== 'all') subs = subs.filter(s => s.status === this.statusFilter);
        subs = this.sortSubmissions(subs);
        this.filteredSubmissions = subs;
        this.selectedSubmissions.clear();
        this.currentPage = 1;
        this.renderAll();
    }

    _getCourseName(slug) { const m = { 'python-ds': 'Python for Data Science', 'ml-az': 'Machine Learning A-Z', 'deep-learning': 'Deep Learning Specialization', 'data-eng': 'Data Engineering Essentials' }; return m[slug] || slug; }
    _getAssignmentName(id) { const m = { '1': 'Assignment 4', '2': 'Quiz 3', '3': 'Assignment 3' }; return m[id] || ''; }

    sortSubmissions(subs) {
        switch (this.sortBy) {
            case 'newest': return subs.sort((a, b) => b.submitDate - a.submitDate);
            case 'oldest': return subs.sort((a, b) => a.submitDate - b.submitDate);
            case 'student-asc': return subs.sort((a, b) => a.studentName.localeCompare(b.studentName));
            default: return subs;
        }
    }

    renderAll() {
        this.renderStatistics();
        document.getElementById('showingCount').textContent = this.filteredSubmissions.length;
        this.renderTable();
        this.renderCards();
        this.renderPagination();
        this.updateBulkBar();
        this.checkEmpty();
    }

    renderStatistics() {
        const t = this.allSubmissions.length;
        console.log("allSubmissions", this.allSubmissions)
        document.getElementById('statTotal').textContent = t;
        document.getElementById('statPending').textContent = this.allSubmissions.filter(s => s.status === 'pending').length;
        document.getElementById('statGraded').textContent = this.allSubmissions.filter(s => s.status === 'graded').length;
        document.getElementById('statLate').textContent = this.allSubmissions.filter(s => s.status === 'late').length;
    }

    renderTable() {
        const tbody = document.getElementById('submissionTableBody');
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredSubmissions.slice(start, start + this.perPage);
        tbody.innerHTML = page.map(s => `
            <tr>
                <td class="col-check"><input type="checkbox" class="sub-checkbox" data-id="${s.id}"></td>
                <td><div class="student-info-cell"><img src="${s.studentAvatar}" class="student-avatar-sm" onerror="this.src='https://ui-avatars.com/api/?name=S&background=6B7280&color=fff&size=72'"><div><span class="student-name-sm">${s.studentName}</span><span class="student-email-sm">${s.studentEmail}</span></div></div></td>
                <td><span class="assignment-name">${s.assignmentName}</span><span class="assignment-desc">${s.assignmentDesc}</span><span class="assignment-desc" style="margin-top:4px;">Submitted: ${this.formatRelative(s.submitDate)}</span></td>
                <td><span class="course-name-td">${s.courseName}</span></td>
                <td><span class="status-badge-assign ${s.status}"><span class="status-dot ${s.status}"></span> ${this.capitalize(s.status)}</span></td>
                <td>${s.status === 'graded' ? `<div class="grade-display"><span class="grade-score ${s.score >= 90 ? 'high' : s.score >= 80 ? 'medium' : 'low'}">${s.score}/100</span><span class="grade-letter">${s.letterGrade}</span></div>` : '<span style="color:var(--color-gray-400);font-size:0.82rem;">—</span>'}</td>
                <td><div class="actions-cell">
                    <button class="assign-action-btn view" title="View Submission" onclick="instructorAssignmentsPage.openViewModal(${s.id})"><i class="fas fa-eye"></i></button>
                    <button class="assign-action-btn download" title="Download Files" onclick="instructorAssignmentsPage.downloadSubmission(${s.id})"><i class="fas fa-download"></i></button>
                    ${s.status !== 'graded' ? `<button class="assign-action-btn grade" title="Grade" onclick="instructorAssignmentsPage.openGradeModal(${s.id})"><i class="fas fa-pen"></i></button>` : `<button class="assign-action-btn grade" title="View/Edit Grade" onclick="instructorAssignmentsPage.openGradeModal(${s.id})"><i class="fas fa-check"></i></button>`}
                </div></td>
            </tr>
        `).join('');
        tbody.querySelectorAll('.sub-checkbox').forEach(cb => cb.addEventListener('change', () => { const id = parseInt(cb.dataset.id); cb.checked ? this.selectedSubmissions.add(id) : this.selectedSubmissions.delete(id); this.updateBulkBar(); }));
    }

    renderCards() {
        const container = document.getElementById('submissionCardsList');
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredSubmissions.slice(start, start + this.perPage);
        container.innerHTML = page.map(s => `
            <div class="submission-card">
                <div class="submission-card-top">
                    <input type="checkbox" class="sub-checkbox" data-id="${s.id}" style="margin-top:4px;">
                    <img src="${s.studentAvatar}" class="student-avatar-sm" onerror="this.src='https://ui-avatars.com/api/?name=S&background=6B7280&color=fff&size=72'">
                    <div class="submission-card-info">
                        <div class="submission-card-student">${s.studentName}</div>
                        <div class="submission-card-email">${s.studentEmail}</div>
                    </div>
                    <span class="status-badge-assign ${s.status}"><span class="status-dot ${s.status}"></span> ${this.capitalize(s.status)}</span>
                </div>
                <div class="submission-card-assignment"><strong>${s.assignmentName}</strong> · ${s.courseName}</div>
                <div class="assignment-desc">${s.assignmentDesc} · Submitted ${this.formatRelative(s.submitDate)}</div>
                ${s.files && s.files.length > 0 ? `<div class="submission-files-preview"><i class="fas fa-paperclip"></i> ${s.files.length} file${s.files.length > 1 ? 's' : ''} attached</div>` : ''}
                ${s.status === 'graded' ? `<div class="grade-display" style="margin-top:8px;"><span class="grade-score ${s.score >= 90 ? 'high' : s.score >= 80 ? 'medium' : 'low'}">${s.score}/100 (${s.letterGrade})</span></div>` : ''}
                <div class="submission-card-footer">
                    <div class="actions-cell">
                        <button class="assign-action-btn view" onclick="instructorAssignmentsPage.openViewModal(${s.id})"><i class="fas fa-eye"></i> View</button>
                        <button class="assign-action-btn download" onclick="instructorAssignmentsPage.downloadSubmission(${s.id})"><i class="fas fa-download"></i></button>
                        ${s.status !== 'graded' ? `<button class="assign-action-btn grade" onclick="instructorAssignmentsPage.openGradeModal(${s.id})"><i class="fas fa-pen"></i> Grade</button>` : `<button class="assign-action-btn grade" onclick="instructorAssignmentsPage.openGradeModal(${s.id})"><i class="fas fa-check"></i> Grade</button>`}
                    </div>
                </div>
            </div>
        `).join('');
        container.querySelectorAll('.sub-checkbox').forEach(cb => cb.addEventListener('change', () => { const id = parseInt(cb.dataset.id); cb.checked ? this.selectedSubmissions.add(id) : this.selectedSubmissions.delete(id); this.updateBulkBar(); }));
    }

    toggleSelectAll(checked) {
        const start = (this.currentPage - 1) * this.perPage;
        const page = this.filteredSubmissions.slice(start, start + this.perPage);
        page.forEach(s => checked ? this.selectedSubmissions.add(s.id) : this.selectedSubmissions.delete(s.id));
        document.querySelectorAll('.sub-checkbox').forEach(cb => { cb.checked = checked; });
        document.getElementById('headerCheckbox').checked = checked;
        document.getElementById('selectAllCheckbox').checked = checked;
        this.updateBulkBar();
    }

    updateBulkBar() {
        const c = this.selectedSubmissions.size;
        document.getElementById('bulkSelectedCount').textContent = `${c} selected`;

        document.getElementById('bulkDownloadBtn').disabled = c === 0;
    }

    openViewModal(id) {
        this.currentViewSubmissionId = id;
        const s = this.allSubmissions.find(sub => sub.id === id);
        if (!s) return;

        const modal = document.getElementById('viewSubmissionModal');
        const title = document.getElementById('viewModalTitle');
        const body = document.getElementById('viewModalBody');

        if (!modal || !title || !body) return;

        title.textContent = `Submission: ${s.assignmentName}`;

        const filesHtml = s.files && s.files.length > 0 ? `
            <div class="view-section">
                <h4 class="view-section-title"><i class="fas fa-paperclip"></i> Attached Files (${s.files.length})</h4>
                <div class="files-list">
                    ${s.files.map(file => `
                        <div class="file-item">
                            <div class="file-item-icon">
                                <i class="fas ${this.getFileIcon(file.type || file.name)}"></i>
                            </div>
                            <div class="file-item-info">
                                <div class="file-item-name">${file.name}</div>
                                <div class="file-item-meta">${file.size || 'Unknown size'} · Uploaded ${this.formatRelative(new Date(file.uploadedAt || s.submitDate))}</div>
                            </div>
                            <div class="file-item-actions">
                                <button class="file-action-btn view-file" onclick="instructorAssignmentsPage.viewFile('${file.id || file.name}', '${file.name}')" title="Preview File">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="file-action-btn download-file" onclick="instructorAssignmentsPage.downloadSingleFile(${s.id}, '${file.id || file.name}', '${file.name}')" title="Download File">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="files-bulk-actions">
                    <button class="nav-btn secondary" onclick="instructorAssignmentsPage.downloadAllFiles(${s.id})">
                        <i class="fas fa-download"></i> Download All Files (ZIP)
                    </button>
                </div>
            </div>
        ` : `
            <div class="view-section">
                <h4 class="view-section-title"><i class="fas fa-paperclip"></i> Attached Files</h4>
                <p class="no-files-message">No files attached to this submission.</p>
            </div>
        `;

        body.innerHTML = `
            <div class="view-submission-container">
                <div class="view-header">
                    <div class="view-student-info">
                        <img src="${s.studentAvatar}" class="view-student-avatar" onerror="this.src='https://ui-avatars.com/api/?name=S&background=6B7280&color=fff&size=80'">
                        <div class="view-student-details">
                            <h3>${s.studentName}</h3>
                            <p>${s.studentEmail}</p>
                            <span class="status-badge-assign ${s.status}"><span class="status-dot ${s.status}"></span> ${this.capitalize(s.status)}</span>
                        </div>
                    </div>
                    <div class="view-meta">
                        <div class="view-meta-item">
                            <span class="view-meta-label">Course</span>
                            <span class="view-meta-value">${s.courseName}</span>
                        </div>
                        <div class="view-meta-item">
                            <span class="view-meta-label">Assignment</span>
                            <span class="view-meta-value">${s.assignmentName}</span>
                        </div>
                        <div class="view-meta-item">
                            <span class="view-meta-label">Submitted</span>
                            <span class="view-meta-value">${this.formatRelative(s.submitDate)}</span>
                        </div>
                        ${s.status === 'graded' ? `
                            <div class="view-meta-item">
                                <span class="view-meta-label">Grade</span>
                                <span class="view-meta-value grade-highlight">${s.score}/100 (${s.letterGrade})</span>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <div class="view-section">
                    <h4 class="view-section-title"><i class="fas fa-align-left"></i> Submission Text</h4>
                    <div class="submission-text-content">${this.formatSubmissionText(s.submissionText)}</div>
                </div>

                ${filesHtml}

                ${s.status === 'graded' && s.feedback ? `
                    <div class="view-section">
                        <h4 class="view-section-title"><i class="fas fa-comment-dots"></i> Feedback</h4>
                        <div class="feedback-content">${s.feedback}</div>
                    </div>
                ` : ''}

                <div class="view-actions-footer">
                    ${s.status !== 'graded' ? `
                        <button class="nav-btn primary" onclick="instructorAssignmentsPage.openGradeModal(${s.id}); document.getElementById('viewSubmissionModal').style.display = 'none';">
                            <i class="fas fa-pen"></i> Grade Submission
                        </button>
                    ` : `
                        <button class="nav-btn secondary" onclick="instructorAssignmentsPage.openGradeModal(${s.id}); document.getElementById('viewSubmissionModal').style.display = 'none';">
                            <i class="fas fa-edit"></i> Edit Grade
                        </button>
                    `}
                    <button class="nav-btn secondary" onclick="instructorAssignmentsPage.downloadSubmission(${s.id})">
                        <i class="fas fa-download"></i> Download Files
                    </button>
                </div>
            </div>
        `;

        modal.style.display = 'flex';
    }

    formatSubmissionText(text) {
        if (!text) return '<p class="no-content">No submission text provided.</p>';
        return text
            .replace(/\n/g, '<br>')
            .replace(/(\*\*|__)(.*?)\1/g, '<strong>$2</strong>')
            .replace(/(\*|_)(.*?)\1/g, '<em>$2</em>')
            .replace(/^- (.*)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }

    getFileIcon(filename) {
        const ext = (filename || '').split('.').pop().toLowerCase();
        const iconMap = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'ppt': 'fa-file-powerpoint',
            'pptx': 'fa-file-powerpoint',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'svg': 'fa-file-image',
            'py': 'fa-file-code',
            'js': 'fa-file-code',
            'html': 'fa-file-code',
            'css': 'fa-file-code',
            'java': 'fa-file-code',
            'cpp': 'fa-file-code',
            'c': 'fa-file-code',
            'ipynb': 'fa-file-code',
            'csv': 'fa-file-csv',
            'txt': 'fa-file-alt',
            'md': 'fa-file-alt',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive',
            'tar': 'fa-file-archive',
            'gz': 'fa-file-archive'
        };
        return iconMap[ext] || 'fa-file';
    }

    viewFile(fileId, fileName) {
        console.log("view file", fileId, fileName)
        console.log(this.allSubmissions)
        console.log("this.currentViewSubmissionId", this.currentViewSubmissionId)
        const s = this.allSubmissions.find(sub => sub.id === this.currentViewSubmissionId);
        if (!s) return;

        const file = s.files?.find(f => (f.id || f.name) == fileId);
        if (!file) {
            this.showToast('File not found.');
            return;
        }

        const filePath = file.path || file.url || file.file_path;
        const fullPath = filePath?.startsWith('http') ? filePath : `${baseUrl}${filePath}`;

        const ext = (file.name || fileName).split('.').pop().toLowerCase();
        console.log(fileName, ext)
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext);
        const isPdf = ext === 'pdf';
        const isCode = ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'ts', 'jsx', 'tsx', 'json', 'xml', 'sql', 'rb', 'php', 'go', 'rs', 'swift', 'kt', 'ipynb'].includes(ext);
        const isText = ['txt', 'md', 'csv', 'log', 'yml', 'yaml', 'ini', 'cfg', 'env'].includes(ext);

        let fileContent = '';

        if (isImage && fullPath) {
            fileContent = `
                <div class="file-preview-image-container">
                    <img src="${fullPath}" alt="${fileName}" class="file-preview-image" onerror="this.src='https://via.placeholder.com/800x400/6B7280/FFFFFF?text=Image+Not+Available'">
                </div>
            `;
        } else if (isPdf && fullPath) {
            fileContent = `
                <div class="file-preview-pdf">
                    <iframe src="${fullPath}" class="pdf-viewer" frameborder="0"></iframe>
                </div>
            `;
        } else if ((isCode || isText) && fullPath) {
            fileContent = `
                <div class="file-preview-code">
                    <div class="code-header">
                        <span class="code-filename"><i class="fas ${this.getFileIcon(fileName)}"></i> ${fileName}</span>
                        <span class="code-lang">${ext.toUpperCase()}</span>
                    </div>
                    <pre class="code-block"><code id="codeContent">Loading...</code></pre>
                </div>
            `;
            setTimeout(() => {
                fetch(fullPath)
                    .then(response => response.text())
                    .then(text => {
                        const codeElement = document.getElementById('codeContent');
                        if (codeElement) {
                            codeElement.textContent = text;
                        }
                    })
                    .catch(() => {
                        const codeElement = document.getElementById('codeContent');
                        if (codeElement) {
                            codeElement.textContent = 'Error loading file content.';
                        }
                    });
            }, 100);
        } else if (fullPath) {
            fileContent = `
                <div class="file-preview-unsupported">
                    <i class="fas ${this.getFileIcon(fileName)} file-unsupported-icon"></i>
                    <p>Preview not available for this file type.</p>
                    <button class="nav-btn primary" onclick="instructorAssignmentsPage.downloadSingleFile(${s.id}, '${fileId}', '${fileName}')">
                        <i class="fas fa-download"></i> Download ${fileName}
                    </button>
                </div>
            `;
        } else {
            fileContent = `
                <div class="file-preview-unsupported">
                    <i class="fas fa-exclamation-triangle file-unsupported-icon"></i>
                    <p>File not available for preview.</p>
                </div>
            `;
        }

        const fileViewerModal = document.getElementById('fileViewerModal');
        const fileViewerTitle = document.getElementById('fileViewerTitle');
        const fileViewerBody = document.getElementById('fileViewerBody');
        const fileViewerDownloadBtn = document.getElementById('fileViewerDownloadBtn');

        if (!fileViewerModal || !fileViewerTitle || !fileViewerBody) return;

        fileViewerTitle.textContent = `File Preview: ${fileName}`;
        fileViewerBody.innerHTML = fileContent;

        if (fileViewerDownloadBtn) {
            fileViewerDownloadBtn.onclick = () => this.downloadSingleFile(s.id, fileId, fileName);
        }

        fileViewerModal.style.display = 'flex';
    }

    downloadSubmission(id) {
        const s = this.allSubmissions.find(sub => sub.id === id);
        if (!s) return;

        if (s.files && s.files.length > 0) {
            if (s.files.length === 1) {
                this.downloadSingleFile(s.id, s.files[0].id, s.files[0].name);
            } else {
                this.downloadAllFiles(s.id);
            }
        } else {
            this.showToast('No files available for download.');
        }
    }

    downloadSingleFile(submissionId, fileId, fileName) {
        const s = this.allSubmissions.find(sub => sub.id == submissionId);
        if (!s) return;

        const file = s.files?.find(f => (f.id || f.name) == fileId);
        if (!file) {
            this.showToast('File not found.');
            return;
        }

        const filePath = file.path || file.url || file.file_path;

        if (!filePath) {
            this.showToast('File path not available.');
            return;
        }

        const link = document.createElement('a');
        link.href = filePath.startsWith('http') ? filePath : `${baseUrl}${filePath}`;
        link.download = fileName || file.name;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showToast(`Downloading ${fileName || file.name}...`);
    }

    downloadAllFiles(id) {
        const s = this.allSubmissions.find(sub => sub.id == id);
        if (!s) return;

        const downloadUrl = `${baseUrl}/api/v1/instructor/assignments/${id}/download/`;

        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `submission_${id}_files.zip`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showToast(`Downloading all files for ${s.studentName}'s submission...`);
    }

    bulkDownload() {
        const selectedIds = Array.from(this.selectedSubmissions);
        if (selectedIds.length == 0) {
            this.showToast('No submissions selected.');
            return;
        }

        const idsParam = selectedIds.join(',');
        const downloadUrl = `${baseUrl}/api/v1/instructor/assignments/bulk-download/?ids=${idsParam}`;

        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `bulk_submissions_${Date.now()}.zip`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showToast(`Downloading ${selectedIds.length} submissions...`);
    }

    openGradeModal(id) {
        this.currentGradeId = id;
        const s = this.allSubmissions.find(sub => sub.id == id);
        if (!s) return;
        document.getElementById('gradeModalTitle').textContent = `Grade: ${s.assignmentName}`;
        document.getElementById('gradeModalBody').innerHTML = `
            <div class="grade-preview">
                <div class="grade-preview-header">
                    <img src="${s.studentAvatar}" class="grade-preview-avatar" onerror="this.src='https://ui-avatars.com/api/?name=S&background=6B7280&color=fff&size=80'">
                    <div class="grade-preview-info"><strong>${s.studentName}</strong>${s.courseName} · Submitted ${this.formatRelative(s.submitDate)}</div>
                </div>
                <div class="grade-preview-files">
                    ${s.files && s.files.length > 0 ? `
                        <div class="grade-files-summary">
                            <i class="fas fa-paperclip"></i>
                            <span>${s.files.length} file(s) attached:</span>
                            <span class="grade-files-list">${s.files.map(f => f.name).join(', ')}</span>
                            <button class="btn-link" onclick="instructorAssignmentsPage.openViewModal(${s.id}); document.getElementById('gradeModal').style.display = 'none';">
                                View all files
                            </button>
                        </div>
                    ` : ''}
                </div>
                <div class="grade-preview-submission">${s.submissionText}</div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Score (0-100)</label><input type="number" id="gradeScore" class="form-input" value="${s.score || ''}" min="0" max="100" placeholder="e.g. 85"></div>
                <div class="form-group"><label>Letter Grade</label><select id="gradeLetter" class="form-input"><option value="">Auto</option><option value="A" ${s.letterGrade==='A'?'selected':''}>A (90-100)</option><option value="B" ${s.letterGrade==='B'?'selected':''}>B (80-89)</option><option value="C" ${s.letterGrade==='C'?'selected':''}>C (70-79)</option><option value="D" ${s.letterGrade==='D'?'selected':''}>D (60-69)</option><option value="F" ${s.letterGrade==='F'?'selected':''}>F (0-59)</option></select></div>
            </div>
            <div class="form-group"><label>Feedback</label><textarea id="gradeFeedback" class="form-input form-textarea" rows="4" placeholder="Leave feedback for the student...">${s.feedback || ''}</textarea></div>
        `;
        document.getElementById('gradeModal').style.display = 'flex';
    }

    async submitGrade() {
        if (!this.currentGradeId) return;
        const s = this.allSubmissions.find(sub => sub.id == this.currentGradeId);
        if (!s) return;
        const score = parseInt(document.getElementById('gradeScore').value) || 0;
        const letter = document.getElementById('gradeLetter').value || (score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F');
        const feedback = document.getElementById('gradeFeedback').value.trim();
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + `/api/v1/instructor/assignments/grade/${this.currentGradeId}/`,
                {
                    method: "PATCH",
                    body:JSON.stringify({"feedback":feedback, "score":score})
                }
            );

            const data = await response.json();
            if (!response.ok) {
                console.log(data)
                throw new Error("Failed to grade.");
            }

            console.log(data)
            s.status = 'graded';
            s.score = score;
            s.letterGrade = letter;
            s.feedback = feedback;
            s.gradedDate = new Date();
            document.getElementById('gradeModal').style.display = 'none';
            this.applyFilters();
            this.showToast(`Grade submitted: ${score}/100 (${letter})`);

        } catch (error) {
            console.error("Error grading assignment:", error);

        }


    }

    bulkGrade() {
        const selectedIds = Array.from(this.selectedSubmissions);
        if (selectedIds.length === 0) {
            this.showToast('No submissions selected.');
            return;
        }
        this.showToast(`Bulk grading ${selectedIds.length} submissions...`);
    }

    renderPagination() {
        const total = Math.ceil(this.filteredSubmissions.length / this.perPage);
        const c = document.getElementById('pageNumbers');
        if (total <= 1) { c.innerHTML = ''; document.getElementById('prevPage').disabled = true; document.getElementById('nextPage').disabled = true; return; }
        document.getElementById('prevPage').disabled = this.currentPage <= 1;
        document.getElementById('nextPage').disabled = this.currentPage >= total;
        c.innerHTML = Array.from({ length: total }, (_, i) => `<button class="page-number ${i + 1 === this.currentPage ? 'active' : ''}" data-page="${i + 1}">${i + 1}</button>`).join('');
        c.querySelectorAll('.page-number').forEach(b => b.addEventListener('click', () => { this.currentPage = parseInt(b.dataset.page); this.renderTable(); this.renderCards(); this.renderPagination(); }));
    }

    changePage(d) { const total = Math.ceil(this.filteredSubmissions.length / this.perPage); const np = this.currentPage + d; if (np >= 1 && np <= total) { this.currentPage = np; this.renderTable(); this.renderCards(); this.renderPagination(); } }

    checkEmpty() {
        const show = this.filteredSubmissions.length == 0;
        document.getElementById('submissionTableBody').style.display = show ? 'none' : '';
        document.getElementById('submissionCardsList').style.display = show ? 'none' : '';
        document.getElementById('pagination').style.display = show ? 'none' : '';
        document.getElementById('emptyState').style.display = show ? 'block' : 'none';
        document.getElementById('resultsInfo').style.display = show ? 'none' : '';
        document.getElementById('bulkActionsBar').style.display = show ? 'none' : '';
        if (show) document.getElementById('emptyMessage').textContent = this.searchQuery || this.statusFilter !== 'all' ? 'No submissions match your filters. Try adjusting your search or status.' : 'Submissions will appear here when students submit their assignments.';
    }

    showSkeletons() { document.getElementById('submissionTableBody').innerHTML = Array(8).fill('<tr><td colspan="7"><div class="skeleton-line" style="height:50px;"></div></td></tr>').join(''); }
    hideLoader() { document.getElementById('loadingOverlay')?.classList.add('hidden'); }
    capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
    formatRelative(d) { const diff = Math.floor((Date.now() - d) / 3600000); if (diff < 1) return 'Just now'; if (diff < 24) return diff + 'h ago'; const days = Math.floor(diff / 24); if (days === 1) return 'Yesterday'; if (days < 7) return days + 'd ago'; return Math.floor(days / 7) + 'w ago'; }
    showToast(m) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = m;
        container.appendChild(t);
        requestAnimationFrame(() => { t.style.opacity = '1'; t.style.transform = 'translateY(0)'; });
        setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3000);
    }
}

let instructorAssignmentsPage;
document.addEventListener('DOMContentLoaded', () => { instructorAssignmentsPage = new InstructorAssignmentsPage(); });
