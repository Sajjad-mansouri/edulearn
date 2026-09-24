// ============================================
// CERTIFICATES PAGE CONTROLLER
// ============================================

class CertificatesPage {
    constructor() {
        this.searchQuery = '';
        this.activeTab = 'all';
        this.allCertificates = [];
        this.filteredCertificates = [];
        this.currentCertificate = null;
        this.isDownloading = false;
        this.isLoadingPDF = false;
        this.pdfUrl = null;

        this.init();
    }

    async init() {

        this.bindEvents();

        try {
            await this.loadCertificates();
        } catch (error) {
            console.error('Error during initialization:', error);
            this.allCertificates = this.getDummyCertificates();
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
        const searchInput = document.getElementById('certificateSearch');
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

        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.activeTab = btn.dataset.tab;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.applyFilters();
            });
        });

        // Modal
        document.getElementById('modalCloseBtn')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalOverlay')?.addEventListener('click', () => this.closeModal());
        document.getElementById('downloadBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.downloadCertificate();
        });
        document.getElementById('shareBtn')?.addEventListener('click', () => this.shareCertificate());

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    // ============================================
    // DATA LOADING
    // ============================================
    async loadCertificates() {

        this.showSkeletons();

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + '/api/v1/enrollment/certificates/',
                {
                    method: "GET",
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }
            );

            if (response && response.ok) {
                const data = await response.json();


                // Handle paginated response
                const certificates = data.results || data || [];
                this.allCertificates = certificates.map(item => this.mapApiItemToCertificate(item));
                this.applyFilters();
            } else {
                throw new Error('Failed to fetch certificates');
            }
        } catch (error) {
            console.error('Error loading certificates:', error);
            await new Promise(resolve => setTimeout(resolve, 600));
            this.allCertificates = this.getDummyCertificates();
            this.applyFilters();
        }
    }

    // Map API item structure to our internal structure
    mapApiItemToCertificate(apiItem) {
        return {
            id: apiItem.id,
            certificateId: apiItem.certificate_number || `CERT-${Date.now()}-${apiItem.id}`,
            courseTitle: apiItem.course_title || apiItem.title || 'Untitled Course',
            courseSlug: apiItem.course_slug || apiItem.slug || '',
            instructor: apiItem.instructor || apiItem.instructor_name || 'Unknown Instructor',
            completionDate: new Date(apiItem.completion_date || apiItem.completed_at || apiItem.issued_date),
            progress: apiItem.progress || 0,
            completed: apiItem.completed === true || apiItem.progress >= 100,
            design: apiItem.design || this.getDesignForId(apiItem.id),
            studentName: apiItem.student_name || 'Student',
            downloadUrl: apiItem.download_url || null,
            verificationUrl: apiItem.verification_url || null
        };
    }

    getDesignForId(id) {
        const designs = ['certificate-design-1', 'certificate-design-2', 'certificate-design-3', 'certificate-design-4'];
        return designs[id % designs.length];
    }

    // ============================================
    // DUMMY DATA (DELETE WHEN ENDPOINTS EXIST)
    // ============================================
    getDummyCertificates() {
        const now = Date.now();
        return [];
    }

    // ============================================
    // FILTERING
    // ============================================
    applyFilters() {
        let certificates = [...this.allCertificates];

        // Apply tab filter
        if (this.activeTab === 'completed') {
            certificates = certificates.filter(c => c.completed);
        } else if (this.activeTab === 'in-progress') {
            certificates = certificates.filter(c => !c.completed);
        }

        // Apply search
        if (this.searchQuery) {
            certificates = certificates.filter(cert =>
                cert.courseTitle.toLowerCase().includes(this.searchQuery) ||
                cert.instructor.toLowerCase().includes(this.searchQuery) ||
                cert.certificateId.toLowerCase().includes(this.searchQuery) ||
                cert.studentName.toLowerCase().includes(this.searchQuery)
            );
        }

        this.filteredCertificates = certificates;
        this.renderAll();
    }

    // ============================================
    // RENDER ALL
    // ============================================
    renderAll() {
        this.renderResultsInfo();
        this.renderCertificatesGrid();
        this.checkEmptyState();
        this.updateHeaderStats();
    }

    renderResultsInfo() {
        const showingCount = document.getElementById('showingCount');
        if (showingCount) {
            showingCount.textContent = this.filteredCertificates.length;
        }
    }

    updateHeaderStats() {
        const totalCerts = document.getElementById('totalCerts');
        if (totalCerts) {
            totalCerts.textContent = this.allCertificates.filter(c => c.completed).length;
        }
    }

    // ============================================
    // RENDER CERTIFICATES GRID
    // ============================================
    renderCertificatesGrid() {
        const container = document.getElementById('certificatesGrid');
        if (!container) return;

        container.innerHTML = this.filteredCertificates.map(cert => this.createCertificateCard(cert)).join('');

        // Bind card events
        container.querySelectorAll('.certificate-thumbnail').forEach(el => {
            el.addEventListener('click', (e) => {
                const id = parseInt(el.dataset.id);
                const cert = this.allCertificates.find(c => c.id === id);
                if (cert && cert.completed) {
                    this.openCertificateModal(cert);
                }
            });
        });

        container.querySelectorAll('.view-certificate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                const cert = this.allCertificates.find(c => c.id === id);
                if (cert && cert.completed) {
                    this.openCertificateModal(cert);
                }
            });
        });

        container.querySelectorAll('.download-certificate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                const id = parseInt(btn.dataset.id);
                const cert = this.allCertificates.find(c => c.id === id);
                if (cert && cert.completed) {
                    this.downloadCertificate(cert);
                }
            });
        });
    }

    createCertificateCard(cert) {
        const formattedDate = this.formatDate(cert.completionDate);

        return `
            <div class="certificate-card" data-id="${cert.id}">
                <div class="certificate-thumbnail ${cert.design}" data-id="${cert.id}">
                    <div class="certificate-mini">
                        <i class="fas fa-graduation-cap certificate-mini-logo"></i>
                        <div class="certificate-mini-title">Certificate</div>
                        <div class="certificate-mini-subtitle">of Completion</div>
                    </div>
                    ${cert.completed ? `
                        <div class="completed-badge">
                            <i class="fas fa-check-circle"></i> Completed
                        </div>
                    ` : `
                        <div class="certificate-progress-overlay">
                            <div class="progress-percentage">
                                <span class="percentage">${cert.progress}%</span>
                                <span class="label">In Progress</span>
                            </div>
                        </div>
                    `}
                </div>
                <div class="certificate-card-body">
                    <h3 class="certificate-course-title">${cert.courseTitle}</h3>
                    <p class="certificate-instructor">${cert.instructor}</p>
                    <div class="certificate-meta">
                        ${cert.completed ? `
                            <span class="certificate-date">
                                <i class="far fa-calendar-check"></i> ${formattedDate}
                            </span>
                            <span class="certificate-id">${cert.certificateId}</span>
                        ` : `
                            <span class="certificate-date">
                                <i class="fas fa-spinner"></i> ${cert.progress}% complete
                            </span>
                        `}
                    </div>
                    <div class="certificate-card-footer">
                        <button class="view-certificate-btn" data-id="${cert.id}" ${!cert.completed ? 'disabled' : ''}>
                            <i class="fas fa-eye"></i> ${cert.completed ? 'View Certificate' : 'Not Available'}
                        </button>
                        <button class="download-certificate-btn" data-id="${cert.id}" ${!cert.completed ? 'disabled' : ''} title="Download PDF">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================================
    // CERTIFICATE MODAL (View PDF)
    // ============================================
    async openCertificateModal(certificate) {
        this.currentCertificate = certificate;
        const modal = document.getElementById('certificateModal');
        const preview = document.getElementById('certificatePreview');

        if (!modal || !preview) return;

        // Show modal with loading state
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Show loading spinner in preview area
        preview.innerHTML = `
            <div class="pdf-loading">
                <div class="loading-spinner"></div>
                <p>Loading PDF...</p>
            </div>
        `;

        // Reset download button
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download PDF';
            downloadBtn.disabled = true; // Disabled until PDF loads
            downloadBtn.type = 'button';
        }

        // Fetch and display PDF
        await this.loadAndDisplayPDF(certificate, preview, downloadBtn);
    }

    // Load PDF and display in modal
    async loadAndDisplayPDF(certificate, previewElement, downloadBtn) {
        this.isLoadingPDF = true;

        try {
            const downloadUrl = `${baseUrl}/api/v1/enrollment/certificate/${certificate.id}/download/`;



            // Fetch PDF
            const response = await auth.authenticatedRequest(
                downloadUrl,
                {
                    method: "GET",
                }
            );

            if (response && response.ok) {
                const blob = await response.blob();
                const contentType = response.headers.get('Content-Type') || blob.type;

                // Check if response is actually a PDF
                if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
                    // Create blob URL for PDF
                    const pdfBlobUrl = URL.createObjectURL(blob);
                    this.pdfUrl = pdfBlobUrl;

                    // Display PDF in iframe
                    previewElement.innerHTML = `
                        <div class="pdf-viewer-container">
                            <iframe
                                src="${pdfBlobUrl}"
                                class="pdf-viewer-iframe"
                                title="Certificate PDF"
                            ></iframe>
                        </div>
                    `;

                    // Enable download button
                    if (downloadBtn) {
                        downloadBtn.disabled = false;
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download PDF';
                    }


                } else {
                    // Not a PDF, show error
                    previewElement.innerHTML = `
                        <div class="pdf-error">
                            <i class="fas fa-exclamation-circle"></i>
                            <h3>Unable to Load Certificate</h3>
                            <p>The server returned an invalid response. Please try again later.</p>
                        </div>
                    `;

                    // Disable download button
                    if (downloadBtn) {
                        downloadBtn.disabled = true;
                    }

                    this.showToast('Failed to load certificate', 'error');
                }
            } else {
                // Handle error responses
                let errorMessage = 'Failed to load certificate';

                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch (e) {
                    // Response is not JSON
                }

                // Show error in preview
                previewElement.innerHTML = `
                    <div class="pdf-error">
                        <i class="fas fa-exclamation-circle"></i>
                        <h3>Error</h3>
                        <p>${errorMessage}</p>
                    </div>
                `;

                // Disable download button
                if (downloadBtn) {
                    downloadBtn.disabled = true;
                }

                this.showToast(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error loading PDF:', error);

            // Show error in preview
            previewElement.innerHTML = `
                <div class="pdf-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error</h3>
                    <p>Unable to load certificate. Please try again.</p>
                </div>
            `;

            // Disable download button
            if (downloadBtn) {
                downloadBtn.disabled = true;
            }

            this.showToast('Failed to load certificate', 'error');
        } finally {
            this.isLoadingPDF = false;
        }
    }

    closeModal() {
        const modal = document.getElementById('certificateModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }

        // Clean up PDF URL
        if (this.pdfUrl) {
            URL.revokeObjectURL(this.pdfUrl);
            this.pdfUrl = null;
        }

        this.currentCertificate = null;
        this.isDownloading = false;
        this.isLoadingPDF = false;
    }

    // ============================================
    // DOWNLOAD CERTIFICATE
    // ============================================
    async downloadCertificate(certificate = null) {
        const cert = certificate || this.currentCertificate;
        if (!cert || this.isDownloading) return;

        this.isDownloading = true;

        // Update button state
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
            downloadBtn.disabled = true;
        }

        try {
            const downloadUrl = `${baseUrl}/certificate/${cert.id}/download/`;



            const response = await auth.authenticatedRequest(
                downloadUrl,
                {
                    method: "GET",
                }
            );

            if (response && response.ok) {
                const blob = await response.blob();
                const contentType = response.headers.get('Content-Type') || blob.type;

                if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
                    // Create download link
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${cert.certificateId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);

                    this.showToast('Certificate downloaded successfully');
                } else {
                    throw new Error('Invalid response from server');
                }
            } else if (response && response.status === 404) {
                throw new Error('Certificate not found');
            } else if (response && response.status === 403) {
                throw new Error('You do not have permission to download this certificate');
            } else if (response && response.status === 401) {
                throw new Error('Please login to download certificate');
            } else {
                throw new Error('Failed to download certificate');
            }

        } catch (error) {
            console.error('Error downloading certificate:', error);
            this.showToast(error.message || 'Error downloading certificate', 'error');
        } finally {
            this.isDownloading = false;

            // Reset button state
            if (downloadBtn) {
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download PDF';
                downloadBtn.disabled = false;
            }
        }
    }

    shareCertificate() {
        if (!this.currentCertificate) return;

        const cert = this.currentCertificate;
        const shareText = `I earned a certificate in ${cert.courseTitle} from EduLearn! 🎓`;
        const shareUrl = cert.verificationUrl || `${window.location.origin}/certificates/verify/${cert.certificateId}`;

        if (navigator.share) {
            navigator.share({
                title: 'My Certificate',
                text: shareText,
                url: shareUrl
            }).catch(console.error);
        } else {
            // Fallback: Copy to clipboard
            navigator.clipboard.writeText(`${shareText} ${shareUrl}`)
                .then(() => this.showToast('Share link copied to clipboard!'))
                .catch(() => this.showToast('Unable to share certificate', 'error'));
        }
    }

    // ============================================
    // EMPTY STATE
    // ============================================
    checkEmptyState() {
        const grid = document.getElementById('certificatesGrid');
        const empty = document.getElementById('emptyState');
        const resultsInfo = document.getElementById('resultsInfo');

        if (!grid || !empty || !resultsInfo) return;

        if (this.filteredCertificates.length === 0) {
            grid.style.display = 'none';
            empty.style.display = 'block';
            resultsInfo.style.display = 'none';
        } else {
            grid.style.display = '';
            empty.style.display = 'none';
            resultsInfo.style.display = '';
        }
    }

    // ============================================
    // SKELETONS AND LOADER
    // ============================================
    showSkeletons() {
        const grid = document.getElementById('certificatesGrid');
        if (grid) {
            grid.innerHTML = Array(6).fill(`
                <div class="certificate-card-skeleton">
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


        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
            loadingOverlay.style.visibility = 'hidden';
            loadingOverlay.style.opacity = '0';
            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.add('d-none');
            loadingOverlay.setAttribute('hidden', 'true');
        }

        const loaderSelectors = [
            '.loader', '.loading', '.spinner', '.preloader',
            '.loading-overlay', '.loading-screen', '.page-loader',
            '.loader-wrapper', '.loading-spinner',
            '[class*="loader"]', '[class*="loading"]', '[class*="spinner"]',
            '[id*="loader"]', '[id*="loading"]', '[id*="spinner"]'
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

    // ============================================
    // UTILITIES
    // ============================================
    formatDate(date) {
        if (!date) return '';
        return new Date(date).toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        });
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

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            console.warn('Toast container not found');
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast-popup toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
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
let certificatesPage;

document.addEventListener('DOMContentLoaded', () => {


    try {
        certificatesPage = new CertificatesPage();

    } catch (error) {
        console.error('Failed to initialize CertificatesPage:', error);

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

    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
        loadingOverlay.style.visibility = 'hidden';
        loadingOverlay.style.opacity = '0';
        loadingOverlay.remove();
    }
}, 3000);
