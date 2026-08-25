// ============================================
// Instructor Registration - Complete JavaScript
// ============================================

class InstructorRegistration {
    constructor() {
        // API Configuration
        this.auth = new Auth({
            "baseURL": window.location.origin + '/api/v1/account/auth',
            "onLogout": () => {}
        });
        this.baseUrl = window.location.origin;

        // State Management
        this.currentStep = 1;
        this.totalSteps = 4;
        this.userData = null;
        this.profileData = null;
        this.isAuthenticated = false;
        this.isInstructor = false;
        this.applicationStatus = null;
        this.formData = {
            skills: [],
            experiences: [],
            educations: []
        };

        // Skill suggestions
        this.skillSuggestions = [
            'Python', 'JavaScript', 'Java', 'C++', 'React', 'Node.js',
            'Django', 'Flask', 'Machine Learning', 'Data Science',
            'AWS', 'Docker', 'Kubernetes', 'SQL', 'MongoDB',
            'UI/UX Design', 'Photoshop', 'Figma', 'Web Development',
            'Mobile Development', 'DevOps', 'Cloud Computing',
            'Artificial Intelligence', 'Blockchain', 'Cybersecurity'
        ];

        this.initialize();
    }

    async initialize() {
        this.showLoading();
        this.bindEvents();

        try {
            // Check authentication status
            await this.checkUserStatus();

            // If authenticated and not instructor, fetch profile data
            if (this.isAuthenticated && !this.isInstructor) {
                await this.fetchProfileData();
                await this.checkApplicationStatus();
            }

            // Initialize form based on status
            this.initializeForm();
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Failed to initialize the page. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    bindEvents() {
        // Navigation buttons
        const nextBtn = document.getElementById('nextBtn');
        const prevBtn = document.getElementById('prevBtn');
        const submitBtn = document.getElementById('submitBtn');
        const redirectHomeBtn = document.getElementById('redirectHomeBtn');

        if (nextBtn) nextBtn.addEventListener('click', () => this.nextStep());
        if (prevBtn) prevBtn.addEventListener('click', () => this.prevStep());
        if (submitBtn) submitBtn.addEventListener('click', () => this.submitApplication());
        if (redirectHomeBtn) {
            redirectHomeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/';
            });
        }

        // Dynamic entries
        const addExperienceBtn = document.getElementById('addExperienceBtn');
        const addEducationBtn = document.getElementById('addEducationBtn');

        if (addExperienceBtn) addExperienceBtn.addEventListener('click', () => this.addExperienceEntry());
        if (addEducationBtn) addEducationBtn.addEventListener('click', () => this.addEducationEntry());

        // Skills input
        const skillInput = document.getElementById('skillInput');
        if (skillInput) {
            skillInput.addEventListener('keydown', (e) => this.handleSkillInput(e));
            skillInput.addEventListener('input', (e) => this.showSkillSuggestions(e.target.value));
            skillInput.addEventListener('blur', () => {
                setTimeout(() => this.hideSkillSuggestions(), 200);
            });
        }

        // Biography character count
        const biography = document.getElementById('biography');
        if (biography) {
            biography.addEventListener('input', (e) => this.updateCharacterCount(e.target));
        }

        // Form validation
        const instructorForm = document.getElementById('instructorForm');
        if (instructorForm) {
            instructorForm.addEventListener('input', (e) => this.validateField(e.target));
        }

        // Close skill suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.skills-input-container')) {
                this.hideSkillSuggestions();
            }
        });

        // Update review summary when navigating to step 4
        const reviewStep = document.querySelector('.form-step[data-step="4"]');
        if (reviewStep) {
            const observer = new MutationObserver(() => {
                if (reviewStep.classList.contains('active')) {
                    this.updateReviewSummary();
                }
            });
            observer.observe(reviewStep, { attributes: true, attributeFilter: ['class'] });
        }
    }

    async checkUserStatus() {
        try {
            const response = await this.auth.authenticatedRequest(
                this.baseUrl + "/api/v1/account/auth/current_user/",
                { method: "GET" }
            );

            if (!response.ok) {
                // User is not authenticated
                this.isAuthenticated = false;
                this.userData = null;
                return;
            }

            this.userData = await response.json();
            this.isAuthenticated = true;

            if (this.userData.is_instructor) {
                this.isInstructor = true;
                this.showAlreadyInstructor();
            }

        } catch (error) {
            // User is not authenticated or endpoint not available
            console.log('User is not authenticated');
            this.isAuthenticated = false;
            this.userData = null;
        }
    }

    async fetchProfileData() {
        if (!this.isAuthenticated) return;

        try {
            const response = await this.auth.authenticatedRequest(
                this.baseUrl + "/api/v1/account/profile",
                { method: "GET" }
            );

            if (response.ok) {
                this.profileData = await response.json();
                console.log('Profile data fetched:', this.profileData);
            }

        } catch (error) {
            console.warn('Profile data fetch failed:', error);
            this.profileData = null;
        }
    }

    async checkApplicationStatus() {
        if (!this.isAuthenticated) {
            this.applicationStatus = 'none';
            return;
        }

        try {
            const response = await this.auth.authenticatedRequest(
                this.baseUrl + "/api/v1/instructor/application/status/",
                { method: "GET" }
            );

            if (response.ok) {
                const data = await response.json();
                this.applicationStatus = data.status || 'none';

                if (this.applicationStatus === 'pending') {
                    this.showPendingApplication();
                } else if (this.applicationStatus === 'rejected') {
                    this.showRejectedApplication(data.reason);
                }
            }

        } catch (error) {
            // If endpoint doesn't exist, assume no application
            console.warn('Application status check failed:', error);
            this.applicationStatus = 'none';
        }
    }

    initializeForm() {
        // If user is already an instructor, don't show the form
        if (this.isInstructor) {
            return;
        }

        // If application is pending, don't show the form
        if (this.applicationStatus === 'pending') {
            return;
        }

        // Show registration container
        const registrationContainer = document.getElementById('registrationContainer');
        if (registrationContainer) {
            registrationContainer.style.display = 'block';
        }

        // Populate personal details based on authentication status
        this.populatePersonalDetails();

        // Populate profile data for authenticated users
        if (this.isAuthenticated && this.profileData) {
            this.populateProfileData();
        }

        // Add initial empty entries if no existing data
        this.addExperienceEntry();
        this.addEducationEntry();

        // Show first step
        this.showStep(1);
    }

    populatePersonalDetails() {
        const usernameField = document.getElementById('username');
        const emailField = document.getElementById('email');
        const firstNameField = document.getElementById('firstName');
        const lastNameField = document.getElementById('lastName');
        const guestNote = document.getElementById('guestNote');

        if (this.isAuthenticated && this.userData) {
            // Populate fields with user data (readonly)
            if (usernameField) {
                usernameField.value = this.userData.username || '';
                usernameField.readOnly = true;
                usernameField.style.backgroundColor = '#f3f4f6';
            }

            if (emailField) {
                emailField.value = this.userData.email || '';
                emailField.readOnly = true;
                emailField.style.backgroundColor = '#f3f4f6';
            }

            if (firstNameField) {
                firstNameField.value = this.userData.first_name || '';
                firstNameField.readOnly = true;
                firstNameField.style.backgroundColor = '#f3f4f6';
            }

            if (lastNameField) {
                lastNameField.value = this.userData.last_name || '';
                lastNameField.readOnly = true;
                lastNameField.style.backgroundColor = '#f3f4f6';
            }

            // Hide guest note for authenticated users
            if (guestNote) {
                guestNote.style.display = 'none';
            }

        } else {
            // Make fields editable for unauthenticated users
            if (usernameField) {
                usernameField.readOnly = false;
                usernameField.placeholder = 'Enter your username';
                usernameField.style.backgroundColor = '';
            }

            if (emailField) {
                emailField.readOnly = false;
                emailField.placeholder = 'Enter your email';
                emailField.style.backgroundColor = '';
            }

            if (firstNameField) {
                firstNameField.readOnly = false;
                firstNameField.placeholder = 'Enter your first name';
                firstNameField.style.backgroundColor = '';
            }

            if (lastNameField) {
                lastNameField.readOnly = false;
                lastNameField.placeholder = 'Enter your last name';
                lastNameField.style.backgroundColor = '';
            }

            // Show guest note
            if (guestNote) {
                guestNote.style.display = 'flex';
            }
        }
    }

    populateProfileData() {
        if (!this.profileData) return;

        // Populate website
        const websiteField = document.getElementById('website');
        if (websiteField && this.profileData.website) {
            websiteField.value = this.profileData.website;
        }

        // Populate country
        const countryField = document.getElementById('country');
        if (countryField && this.profileData.country) {
            countryField.value = this.profileData.country;
        }

        // Populate linkedin
        const linkedinField = document.getElementById('linkedin');
        if (linkedinField && this.profileData.linkedin) {
            linkedinField.value = this.profileData.linkedin;
        }

        // Populate github
        const githubField = document.getElementById('github');
        if (githubField && this.profileData.github) {
            githubField.value = this.profileData.github;
        }

        // Populate organization (from company)
        const organizationField = document.getElementById('organization');
        if (organizationField && this.profileData.company) {
            organizationField.value = this.profileData.company;
        }

        // Populate professional title (from job_title)
        const professionalTitleField = document.getElementById('professionalTitle');
        if (professionalTitleField && this.profileData.job_title) {
            professionalTitleField.value = this.profileData.job_title;
        }

        // Populate skills
        if (this.profileData.skills && this.profileData.skills.length > 0) {
            this.formData.skills = this.profileData.skills.map(skill => skill.name);
            this.renderSkills();
        }

        // Populate experiences
        if (this.profileData.experiences && this.profileData.experiences.length > 0) {
            // Clear existing entries first
            const experienceContainer = document.getElementById('experienceContainer');
            if (experienceContainer) {
                experienceContainer.innerHTML = '';
            }

            // Add each experience
            this.profileData.experiences.forEach(exp => {
                this.addExperienceEntry({
                    company: exp.company,
                    position: exp.position,
                    location: exp.location,
                    description: exp.description,
                    start_date: exp.start_date,
                    end_date: exp.end_date,
                    is_current: exp.is_current,
                });
            });
        }

        // Populate educations
        if (this.profileData.educations && this.profileData.educations.length > 0) {
            // Clear existing entries first
            const educationContainer = document.getElementById('educationContainer');
            if (educationContainer) {
                educationContainer.innerHTML = '';
            }

            // Add each education
            this.profileData.educations.forEach(edu => {
                this.addEducationEntry({
                    institution: edu.institution,
                    degree: edu.degree,
                    field_of_study: edu.field_of_study,
                    description: edu.description,
                    start_date: edu.start_date,
                    end_date: edu.end_date,
                });
            });
        }

        // Populate first name and last name from profile if not already set
        if (this.profileData.first_name) {
            const firstNameField = document.getElementById('firstName');
            if (firstNameField) {
                firstNameField.value = this.profileData.first_name;
            }
        }

        if (this.profileData.last_name) {
            const lastNameField = document.getElementById('lastName');
            if (lastNameField) {
                lastNameField.value = this.profileData.last_name;
            }
        }

        if (this.profileData.email) {
            const emailField = document.getElementById('email');
            if (emailField) {
                emailField.value = this.profileData.email;
            }
        }
    }

    showAlreadyInstructor() {
        const statusContainer = document.getElementById('statusContainer');
        if (!statusContainer) return;

        statusContainer.style.display = 'block';
        statusContainer.innerHTML = `
            <div class="status-card">
                <div class="status-icon approved">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="status-content">
                    <h3>You are already an instructor!</h3>
                    <p>Visit your instructor dashboard to manage your courses.</p>
                    <a href="/instructor/dashboard/" class="btn btn-primary" style="margin-top: 15px;">
                        Go to Instructor Dashboard
                    </a>
                </div>
            </div>
        `;
    }

    showPendingApplication() {
        const statusContainer = document.getElementById('statusContainer');
        if (!statusContainer) return;

        statusContainer.style.display = 'block';
        statusContainer.innerHTML = `
            <div class="status-card">
                <div class="status-icon pending">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="status-content">
                    <h3>Application Under Review</h3>
                    <p>Your instructor application is currently under review. We'll notify you once it's been processed.</p>
                    <p><small>Submitted on: ${new Date().toLocaleDateString()}</small></p>
                </div>
            </div>
        `;
    }

    showRejectedApplication(reason) {
        const statusContainer = document.getElementById('statusContainer');
        if (!statusContainer) return;

        statusContainer.style.display = 'block';
        statusContainer.innerHTML = `
            <div class="status-card">
                <div class="status-icon rejected">
                    <i class="fas fa-times-circle"></i>
                </div>
                <div class="status-content">
                    <h3>Application Rejected</h3>
                    <p>Your previous application was rejected for the following reason:</p>
                    <p><strong>${reason || 'Not specified'}</strong></p>
                    <p>You can update your information and resubmit your application.</p>
                </div>
            </div>
        `;
    }

    showStep(step) {
        // Update current step
        this.currentStep = step;

        // Hide all steps
        document.querySelectorAll('.form-step').forEach(el => {
            el.classList.remove('active');
        });

        // Show current step
        const currentStepEl = document.querySelector(`.form-step[data-step="${step}"]`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
        }

        // Update progress bar
        this.updateProgressBar();

        // Update navigation buttons
        this.updateNavigation();

        // If navigating to step 4, update review summary
        if (step === 4) {
            this.updateReviewSummary();
        }

        // Scroll to top of form
        const instructorForm = document.getElementById('instructorForm');
        if (instructorForm) {
            instructorForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    updateProgressBar() {
        // Update step indicators
        document.querySelectorAll('.progress-step').forEach(el => {
            const stepNum = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed');

            if (stepNum === this.currentStep) {
                el.classList.add('active');
            } else if (stepNum < this.currentStep) {
                el.classList.add('completed');
            }
        });

        // Update progress bar fill
        const progressPercentage = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
        const progressBar = document.querySelector('.progress-bar');

        if (progressBar) {
            let progressFill = progressBar.querySelector('.progress-bar-fill');

            if (!progressFill) {
                progressFill = document.createElement('div');
                progressFill.className = 'progress-bar-fill';
                progressBar.appendChild(progressFill);
            }

            progressFill.style.width = `${progressPercentage}%`;
        }
    }

    updateNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');

        if (prevBtn) {
            prevBtn.style.display = this.currentStep > 1 ? 'inline-flex' : 'none';
        }

        if (nextBtn) {
            nextBtn.style.display = this.currentStep < this.totalSteps ? 'inline-flex' : 'none';
        }

        if (submitBtn) {
            submitBtn.style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';
        }
    }

    nextStep() {
        if (this.validateStep(this.currentStep)) {
            if (this.currentStep < this.totalSteps) {
                this.showStep(this.currentStep + 1);
            }
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.showStep(this.currentStep - 1);
        }
    }

    validateStep(step) {
        let isValid = true;

        switch(step) {
            case 1:
                isValid = this.validatePersonalInfo();
                break;
            case 2:
                isValid = this.validateExperience();
                break;
            case 3:
                isValid = this.validateEducationAndSkills();
                break;
            case 4:
                isValid = true; // No validation needed for review step
                break;
        }

        return isValid;
    }

    validatePersonalInfo() {
        let isValid = true;

        // Validate personal details
        const username = document.getElementById('username');
        const email = document.getElementById('email');
        const firstName = document.getElementById('firstName');
        const lastName = document.getElementById('lastName');

        if (username && !username.value) {
            this.showFieldError(username, 'Username is required');
            isValid = false;
        } else if (username) {
            this.clearFieldError(username);
        }

        if (email && !email.value) {
            this.showFieldError(email, 'Email is required');
            isValid = false;
        } else if (email && !this.isValidEmail(email.value)) {
            this.showFieldError(email, 'Please enter a valid email address');
            isValid = false;
        } else if (email) {
            this.clearFieldError(email);
        }

        if (firstName && !firstName.value) {
            this.showFieldError(firstName, 'First name is required');
            isValid = false;
        } else if (firstName) {
            this.clearFieldError(firstName);
        }

        if (lastName && !lastName.value) {
            this.showFieldError(lastName, 'Last name is required');
            isValid = false;
        } else if (lastName) {
            this.clearFieldError(lastName);
        }

        // Validate professional title
        const title = document.getElementById('professionalTitle');
        if (!title.value || title.value.length < 5) {
            this.showFieldError(title, 'Professional title must be at least 5 characters');
            isValid = false;
        } else {
            this.clearFieldError(title);
        }

        // Validate years of experience
        const years = document.getElementById('yearsExperience');
        if (!years.value || years.value < 0 || years.value > 50) {
            this.showFieldError(years, 'Please enter valid years of experience (0-50)');
            isValid = false;
        } else {
            this.clearFieldError(years);
        }

        return isValid;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    validateExperience() {
        let isValid = true;
        const experienceEntries = document.querySelectorAll('#experienceContainer .dynamic-entry');

        if (experienceEntries.length === 0) {
            this.showError('Please add at least one work experience');
            return false;
        }

        experienceEntries.forEach((entry, index) => {
            const company = entry.querySelector('[name="company"]');
            const position = entry.querySelector('[name="position"]');

            if (company && !company.value) {
                this.showFieldError(company, 'Company is required');
                isValid = false;
            } else if (company) {
                this.clearFieldError(company);
            }

            if (position && !position.value) {
                this.showFieldError(position, 'Position is required');
                isValid = false;
            } else if (position) {
                this.clearFieldError(position);
            }
        });

        return isValid;
    }

    validateEducationAndSkills() {
        let isValid = true;

        // Validate skills
        if (this.formData.skills.length === 0) {
            const skillInput = document.getElementById('skillInput');
            this.showFieldError(skillInput, 'Please add at least one skill');
            isValid = false;
        } else {
            const skillInput = document.getElementById('skillInput');
            this.clearFieldError(skillInput);
        }

        // Education is optional
        const educationEntries = document.querySelectorAll('#educationContainer .dynamic-entry');
        educationEntries.forEach((entry, index) => {
            const institution = entry.querySelector('[name="institution"]');
            const degree = entry.querySelector('[name="degree"]');

            if (institution && institution.value && !degree.value) {
                this.showFieldError(degree, 'Degree is required if institution is provided');
                isValid = false;
            } else if (degree && degree.value && !institution.value) {
                this.showFieldError(institution, 'Institution is required if degree is provided');
                isValid = false;
            } else {
                if (institution) this.clearFieldError(institution);
                if (degree) this.clearFieldError(degree);
            }
        });

        return isValid;
    }

    showFieldError(field, message) {
        if (!field) return;

        field.classList.add('error');
        const errorElement = document.getElementById(`${field.id}Error`) ||
                           field.parentElement?.querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    clearFieldError(field) {
        if (!field) return;

        field.classList.remove('error');
        const errorElement = document.getElementById(`${field.id}Error`) ||
                           field.parentElement?.querySelector('.error-message');
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    validateField(field) {
        if (field && field.classList.contains('error')) {
            this.clearFieldError(field);
        }
    }

    addExperienceEntry(data = null) {
        const container = document.getElementById('experienceContainer');
        if (!container) return;

        const entryCount = container.children.length;

        const entry = document.createElement('div');
        entry.className = 'dynamic-entry';
        entry.innerHTML = `
            <div class="entry-header">
                <span class="entry-title">Experience ${entryCount + 1}</span>
                <button type="button" class="btn-remove-entry" onclick="this.closest('.dynamic-entry').remove()">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="entry-grid">
                <div class="form-group">
                    <label>Company <span class="required">*</span></label>
                    <input type="text" name="company" class="form-control" placeholder="Company name" value="${data?.company || ''}">
                </div>
                <div class="form-group">
                    <label>Position <span class="required">*</span></label>
                    <input type="text" name="position" class="form-control" placeholder="Job title" value="${data?.position || ''}">
                </div>
                <div class="form-group">
                    <label>Location</label>
                    <input type="text" name="location" class="form-control" placeholder="City, Country" value="${data?.location || ''}">
                </div>
                <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" name="start_date" class="form-control" value="${data?.start_date || ''}">
                </div>
                <div class="form-group">
                    <label>End Date</label>
                    <input type="date" name="end_date" class="form-control" value="${data?.end_date || ''}">
                </div>
                <div class="form-group">
                    <label>Current Position</label>
                    <label class="checkbox-container">
                        <input type="checkbox" name="is_current" ${data?.is_current ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        <span class="terms-text">I currently work here</span>
                    </label>
                </div>
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea name="description" class="form-control" rows="3" placeholder="Describe your responsibilities and achievements">${data?.description || ''}</textarea>
                </div>
            </div>
        `;

        container.appendChild(entry);
    }

    addEducationEntry(data = null) {
        const container = document.getElementById('educationContainer');
        if (!container) return;

        const entryCount = container.children.length;

        const entry = document.createElement('div');
        entry.className = 'dynamic-entry';
        entry.innerHTML = `
            <div class="entry-header">
                <span class="entry-title">Education ${entryCount + 1}</span>
                <button type="button" class="btn-remove-entry" onclick="this.closest('.dynamic-entry').remove()">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="entry-grid">
                <div class="form-group">
                    <label>Institution</label>
                    <input type="text" name="institution" class="form-control" placeholder="University/School name" value="${data?.institution || ''}">
                </div>
                <div class="form-group">
                    <label>Degree</label>
                    <input type="text" name="degree" class="form-control" placeholder="e.g., Bachelor of Science" value="${data?.degree || ''}">
                </div>
                <div class="form-group full-width">
                    <label>Field of Study</label>
                    <input type="text" name="field_of_study" class="form-control" placeholder="e.g., Computer Science" value="${data?.field_of_study || ''}">
                </div>
                <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" name="start_date" class="form-control" value="${data?.start_date || ''}">
                </div>
                <div class="form-group">
                    <label>End Date</label>
                    <input type="date" name="end_date" class="form-control" value="${data?.end_date || ''}">
                </div>
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea name="description" class="form-control" rows="3" placeholder="Activities, achievements, etc.">${data?.description || ''}</textarea>
                </div>
            </div>
        `;

        container.appendChild(entry);
    }

    handleSkillInput(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const input = event.target;
            const skill = input.value.trim();

            if (skill && !this.formData.skills.includes(skill)) {
                this.formData.skills.push(skill);
                this.renderSkills();
                input.value = '';
                this.hideSkillSuggestions();
            }
        }
    }

    showSkillSuggestions(query) {
        const suggestionsContainer = document.getElementById('skillsSuggestions');
        if (!suggestionsContainer) return;

        if (!query || query.length < 1) {
            this.hideSkillSuggestions();
            return;
        }

        const filtered = this.skillSuggestions
            .filter(skill =>
                skill.toLowerCase().includes(query.toLowerCase()) &&
                !this.formData.skills.includes(skill)
            )
            .slice(0, 5);

        if (filtered.length > 0) {
            suggestionsContainer.innerHTML = filtered
                .map(skill => `<div class="suggestion-item" onclick="instructorRegistration.addSkill('${skill}')">${skill}</div>`)
                .join('');
            suggestionsContainer.style.display = 'block';
        } else {
            this.hideSkillSuggestions();
        }
    }

    hideSkillSuggestions() {
        const suggestionsContainer = document.getElementById('skillsSuggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }

    addSkill(skill) {
        if (!this.formData.skills.includes(skill)) {
            this.formData.skills.push(skill);
            this.renderSkills();
        }
        const skillInput = document.getElementById('skillInput');
        if (skillInput) {
            skillInput.value = '';
        }
        this.hideSkillSuggestions();
    }

    removeSkill(skill) {
        this.formData.skills = this.formData.skills.filter(s => s !== skill);
        this.renderSkills();
    }

    renderSkills() {
        const container = document.getElementById('skillsTags');
        if (!container) return;

        container.innerHTML = this.formData.skills
            .map(skill => `
                <span class="skill-tag">
                    ${skill}
                    <span class="remove-skill" onclick="instructorRegistration.removeSkill('${skill}')">
                        <i class="fas fa-times"></i>
                    </span>
                </span>
            `)
            .join('');
    }

    updateCharacterCount(textarea) {
        const count = textarea.value.length;
        const biographyCount = document.getElementById('biographyCount');

        if (biographyCount) {
            biographyCount.textContent = count;
        }

        if (count > 2000) {
            textarea.value = textarea.value.substring(0, 2000);
            if (biographyCount) {
                biographyCount.textContent = 2000;
            }
        }
    }

    updateReviewSummary() {
        const reviewContent = document.getElementById('reviewContent');
        if (!reviewContent) return;

        // Collect current form data
        const data = this.collectFormData();

        // Build summary HTML
        let summaryHTML = '';

        // Personal Information
        summaryHTML += `
            <div class="review-section">
                <h4>Personal Information</h4>
                <div class="review-item">
                    <span class="review-label">Username:</span>
                    <span class="review-value">${data.personal_info.username || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Email:</span>
                    <span class="review-value">${data.personal_info.email || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Full Name:</span>
                    <span class="review-value">${data.personal_info.first_name} ${data.personal_info.last_name}</span>
                </div>
            </div>
        `;

        // Professional Information
        summaryHTML += `
            <div class="review-section">
                <h4>Professional Information</h4>
                <div class="review-item">
                    <span class="review-label">Professional Title:</span>
                    <span class="review-value">${data.instructor.professional_title || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Organization:</span>
                    <span class="review-value">${data.instructor.organization || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Years of Experience:</span>
                    <span class="review-value">${data.instructor.years_of_experience} years</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Headline:</span>
                    <span class="review-value">${data.instructor.headline || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">Country:</span>
                    <span class="review-value">${data.profile.country || 'Not provided'}</span>
                </div>
            </div>
        `;

        // Skills
        summaryHTML += `
            <div class="review-section">
                <h4>Skills (${data.skills.length})</h4>
                <div class="review-skills">
                    ${data.skills.length > 0
                        ? data.skills.map(skill => `<span class="review-skill-tag">${skill.name}</span>`).join('')
                        : '<span class="review-value">No skills added</span>'}
                </div>
            </div>
        `;

        // Work Experience
        summaryHTML += `
            <div class="review-section">
                <h4>Work Experience (${data.experiences.length})</h4>
                ${data.experiences.length > 0
                    ? data.experiences.map((exp, index) => `
                        <div class="review-entry">
                            <div class="review-item">
                                <span class="review-label">${index + 1}. ${exp.position || 'Position'}:</span>
                                <span class="review-value">${exp.company || 'Company'}</span>
                            </div>
                            ${exp.location ? `
                            <div class="review-item">
                                <span class="review-label">Location:</span>
                                <span class="review-value">${exp.location}</span>
                            </div>` : ''}
                            ${exp.start_date ? `
                            <div class="review-item">
                                <span class="review-label">Period:</span>
                                <span class="review-value">${exp.start_date} - ${exp.is_current ? 'Present' : (exp.end_date || 'N/A')}</span>
                            </div>` : ''}
                        </div>
                    `).join('')
                    : '<div class="review-item"><span class="review-value">No experience added</span></div>'}
            </div>
        `;

        // Education
        summaryHTML += `
            <div class="review-section">
                <h4>Education (${data.educations.length})</h4>
                ${data.educations.length > 0
                    ? data.educations.map((edu, index) => `
                        <div class="review-entry">
                            <div class="review-item">
                                <span class="review-label">${index + 1}. ${edu.degree || 'Degree'}:</span>
                                <span class="review-value">${edu.institution || 'Institution'}</span>
                            </div>
                            ${edu.field_of_study ? `
                            <div class="review-item">
                                <span class="review-label">Field:</span>
                                <span class="review-value">${edu.field_of_study}</span>
                            </div>` : ''}
                            ${edu.start_date ? `
                            <div class="review-item">
                                <span class="review-label">Period:</span>
                                <span class="review-value">${edu.start_date} - ${edu.end_date || 'Present'}</span>
                            </div>` : ''}
                        </div>
                    `).join('')
                    : '<div class="review-item"><span class="review-value">No education added</span></div>'}
            </div>
        `;

        // Links
        summaryHTML += `
            <div class="review-section">
                <h4>Professional Links</h4>
                <div class="review-item">
                    <span class="review-label">Website:</span>
                    <span class="review-value">${data.profile.website || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">LinkedIn:</span>
                    <span class="review-value">${data.profile.linkedin || 'Not provided'}</span>
                </div>
                <div class="review-item">
                    <span class="review-label">GitHub:</span>
                    <span class="review-value">${data.profile.github || 'Not provided'}</span>
                </div>
            </div>
        `;

        // Biography
        summaryHTML += `
            <div class="review-section">
                <h4>Biography</h4>
                <div class="review-biography">
                    ${data.instructor.biography || 'Not provided'}
                </div>
            </div>
        `;

        reviewContent.innerHTML = summaryHTML;
    }

    collectFormData() {
        // Collect all form data into structured object
        const data = {
            is_authenticated: this.isAuthenticated,
            user_id: this.userData?.id || null,
            personal_info: {
                username: document.getElementById('username')?.value || '',
                email: document.getElementById('email')?.value || '',
                first_name: document.getElementById('firstName')?.value || '',
                last_name: document.getElementById('lastName')?.value || '',
            },
            profile: {
                website: document.getElementById('website')?.value || '',
                country: document.getElementById('country')?.value || '',
                linkedin: document.getElementById('linkedin')?.value || '',
                github: document.getElementById('github')?.value || '',
            },
            instructor: {
                headline: document.getElementById('headline')?.value || '',
                biography: document.getElementById('biography')?.value || '',
                professional_title: document.getElementById('professionalTitle')?.value || '',
                organization: document.getElementById('organization')?.value || '',
                years_of_experience: parseInt(document.getElementById('yearsExperience')?.value) || 0,
            },
            skills: this.formData.skills.map(skill => ({ name: skill })),
            experiences: [],
            educations: [],
        };

        // Collect experiences
        document.querySelectorAll('#experienceContainer .dynamic-entry').forEach(entry => {
            const experience = {
                company: entry.querySelector('[name="company"]')?.value || '',
                position: entry.querySelector('[name="position"]')?.value || '',
                location: entry.querySelector('[name="location"]')?.value || '',
                description: entry.querySelector('[name="description"]')?.value || '',
                start_date: entry.querySelector('[name="start_date"]')?.value || null,
                end_date: entry.querySelector('[name="end_date"]')?.value || null,
                is_current: entry.querySelector('[name="is_current"]')?.checked || false,
            };
            data.experiences.push(experience);
        });

        // Collect education
        document.querySelectorAll('#educationContainer .dynamic-entry').forEach(entry => {
            const education = {
                institution: entry.querySelector('[name="institution"]')?.value || '',
                degree: entry.querySelector('[name="degree"]')?.value || '',
                field_of_study: entry.querySelector('[name="field_of_study"]')?.value || '',
                description: entry.querySelector('[name="description"]')?.value || '',
                start_date: entry.querySelector('[name="start_date"]')?.value || null,
                end_date: entry.querySelector('[name="end_date"]')?.value || null,
            };
            data.educations.push(education);
        });

        return data;
    }

async submitApplication() {
    if (!this.validateStep(4)) {
        return;
    }

    try {
        this.showLoading();

        // Prepare form data
        const data = this.collectFormData();

        console.log('Submitting data:', JSON.stringify(data, null, 2));

        const response = await this.auth.authenticatedRequest(
            this.baseUrl + '/api/v1/account/auth/register/instructor/',
            {
                method: 'POST',
                body: JSON.stringify(data)
            }
        );

        if (response && response.ok) {
            this.showSuccess();
            const responseData = await response.json();
            console.log('Response:', responseData);

            // Redirect to homepage after 3 seconds

        } else {
            // Try to parse error response
            let errorMessage = 'Failed to submit application. Please try again.';

            try {
                const errorData = await response.json();
                console.log('Raw error data:', errorData);
                console.log('Error data type:', typeof errorData);
                console.log('Detail type:', typeof errorData.detail);

                // Check if error has detail field
                if (errorData.detail) {
                    console.log('Detail value:', errorData.detail);

                    // Handle string detail
                    if (typeof errorData.detail === 'string') {
                        errorMessage = errorData.detail;
                    }
                    // Handle array of ErrorDetail objects
                    else if (Array.isArray(errorData.detail)) {
                        console.log('Detail is array, length:', errorData.detail.length);

                        if (errorData.detail.length > 0) {
                            const firstError = errorData.detail[0];
                            console.log('First error:', firstError);
                            console.log('First error type:', typeof firstError);

                            // If firstError is a string like "[ErrorDetail(string='...', code='invalid')]"
                            if (typeof firstError === 'string') {
                                console.log('First error is string:', firstError);

                                // Try multiple regex patterns to extract message
                                let match = firstError.match(/string='([^']+)'/);
                                console.log('Match 1:', match);

                                if (match && match[1]) {
                                    errorMessage = match[1];
                                } else {
                                    // Try another pattern
                                    match = firstError.match(/ErrorDetail\(string='([^']+)'/);
                                    console.log('Match 2:', match);

                                    if (match && match[1]) {
                                        errorMessage = match[1];
                                    } else {
                                        // Try to extract anything between quotes
                                        match = firstError.match(/'([^']+)'/);
                                        console.log('Match 3:', match);

                                        if (match && match[1]) {
                                            errorMessage = match[1];
                                        } else {
                                            // If no match, clean up the string
                                            errorMessage = firstError
                                                .replace(/\[ErrorDetail\(/, '')
                                                .replace(/string=/, '')
                                                .replace(/, code=.*$/, '')
                                                .replace(/'/g, '')
                                                .replace(/\)\]$/, '');
                                        }
                                    }
                                }
                            }
                            // If firstError is an object
                            else if (typeof firstError === 'object' && firstError !== null) {
                                if (firstError.message) {
                                    errorMessage = firstError.message;
                                } else if (firstError.string) {
                                    errorMessage = firstError.string;
                                } else if (firstError.detail) {
                                    errorMessage = firstError.detail;
                                }
                            }
                        }
                    }
                    // Handle object detail
                    else if (typeof errorData.detail === 'object' && errorData.detail !== null) {
                        if (errorData.detail.message) {
                            errorMessage = errorData.detail.message;
                        } else if (errorData.detail.string) {
                            errorMessage = errorData.detail.string;
                        } else if (errorData.detail.detail) {
                            errorMessage = errorData.detail.detail;
                        }
                    }
                }
                // Check for message field
                else if (errorData.message) {
                    errorMessage = errorData.message;
                }
                // Check for error field
                else if (errorData.error) {
                    if (typeof errorData.error === 'string') {
                        errorMessage = errorData.error;
                    } else if (typeof errorData.error === 'object' && errorData.error.message) {
                        errorMessage = errorData.error.message;
                    }
                }

                console.log('Extracted error message:', errorMessage);

            } catch (parseError) {
                console.error('Failed to parse error response:', parseError);
            }

            // Check if user is already registered
            if (errorMessage.includes('already registered') ||
                errorMessage.includes('You are already registered')) {
                // Show specific message for already registered users
                this.showAlreadyRegisteredMessage(errorMessage);
            } else {
                // Show generic error
                this.showError(errorMessage);
            }
        }
    } catch (error) {
        console.error('Submission error:', error);
        this.showError('Failed to submit application. Please try again.');
    } finally {
        this.hideLoading();
    }
}

    showAlreadyRegisteredMessage(message) {
        // Hide registration container
        const registrationContainer = document.getElementById('registrationContainer');
        if (registrationContainer) {
            registrationContainer.style.display = 'none';
        }

        // Show status container with already registered message
        const statusContainer = document.getElementById('statusContainer');
        if (statusContainer) {
            statusContainer.style.display = 'block';
            statusContainer.innerHTML = `
                <div class="status-card">
                    <div class="status-icon pending">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="status-content">
                        <h3>Application Already Submitted</h3>
                        <p>${message || 'You are already registered. If approved, we will notify you.'}</p>
                        <p style="margin-top: 10px;">
                            <small>Please wait for our admin team to review your application.</small>
                        </p>
                        <a href="/" class="btn btn-primary" style="margin-top: 15px; display: inline-flex;">
                            <i class="fas fa-home"></i>
                            Go to Homepage
                        </a>
                    </div>
                </div>
            `;
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showSuccess() {
        const registrationContainer = document.getElementById('registrationContainer');
        const successContainer = document.getElementById('successContainer');

        if (registrationContainer) {
            registrationContainer.style.display = 'none';
        }

        if (successContainer) {
            successContainer.style.display = 'flex';

            // Update message based on authentication status
            const pendingInfo = document.getElementById('pendingInfo');

            if (pendingInfo) {
                if (!this.isAuthenticated) {
                    pendingInfo.innerHTML = `
                        <i class="fas fa-envelope"></i>
                        <p>If your application is approved, we'll send you an email with your login credentials to access your instructor account.</p>
                    `;
                } else {
                    pendingInfo.innerHTML = `
                        <i class="fas fa-envelope"></i>
                        <p>We'll notify you by email once your application has been reviewed.</p>
                    `;
                }
            }
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast toast-error';
        toast.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize the registration page
let instructorRegistration;

document.addEventListener('DOMContentLoaded', () => {
    instructorRegistration = new InstructorRegistration();
});

// Add review summary styles
const reviewStyles = document.createElement('style');
reviewStyles.textContent = `
    .review-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #e5e7eb;
    }

    .review-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }

    .review-section h4 {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 10px;
    }

    .review-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f3f4f6;
    }

    .review-item:last-child {
        border-bottom: none;
    }

    .review-label {
        font-weight: 500;
        color: #6b7280;
        flex-shrink: 0;
        margin-right: 15px;
    }

    .review-value {
        font-weight: 500;
        color: #111827;
        text-align: right;
        word-break: break-word;
    }

    .review-skills {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 5px 0;
    }

    .review-skill-tag {
        display: inline-block;
        padding: 4px 10px;
        background: #eef2ff;
        color: #4f46e5;
        border-radius: 15px;
        font-size: 13px;
        font-weight: 500;
    }

    .review-entry {
        margin-bottom: 15px;
        padding: 10px;
        background: #f9fafb;
        border-radius: 6px;
    }

    .review-entry:last-child {
        margin-bottom: 0;
    }

    .review-biography {
        padding: 10px;
        background: #f9fafb;
        border-radius: 6px;
        font-size: 14px;
        color: #374151;
        line-height: 1.6;
        max-height: 150px;
        overflow-y: auto;
        word-break: break-word;
    }
`;
document.head.appendChild(reviewStyles);
