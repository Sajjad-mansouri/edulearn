// ============================================
// INSTRUCTOR PROFILE PAGE CONTROLLER
// ============================================


function mapInstructorProfile(data) {
    // Handle nested profile structure
    const profileData = data.profile || data;
    const userData = profileData.user || profileData;

    return {
        id: data.id,
        // Basic Profile
        first_name: profileData.first_name || userData.first_name || "",
        last_name: profileData.last_name || userData.last_name || "",
        email: profileData.email || userData.email || "",
        avatar_url: profileData.avatar || profileData.avatar_url || userData.avatar || "",
        cover_url: data.cover || data.cover_url || "",
        website: profileData.website || "",
        country: profileData.country || "",
        timezone: profileData.timezone || "",
        language: profileData.language || "",
        company: profileData.company || "",
        job_title: profileData.job_title || "",

        // Instructor Specific
        headline: data.headline || "",
        biography: data.biography || data.bio || "",
        professional_title: data.professional_title || "",
        organization: data.organization || "",
        years_of_experience: data.years_of_experience || 0,
        introduction_video: data.introduction_video || "",
        resume: data.resume || "",
        application_status: data.application_status || "pending",
        is_verified: data.is_verified || false,
        verification_date: data.verification_date || null,
        rejection_reason: data.rejection_reason || "",

        // Collections - handle both nested and flat structures
        skills: (profileData.skills || data.skills || []).map(item =>
            typeof item === 'string' ? item : (item.name || item.skill || item.title || '')
        ).filter(Boolean),

        education: (profileData.educations || profileData.education || data.educations || data.education || []).map(item => ({
            id: item.id,
            school: item.institution || item.school || "",
            degree: item.degree || "",
            field: item.field_of_study || item.field || "",
            startDate: item.start_date || item.startDate || "",
            endDate: item.end_date || item.endDate || "",
            description: item.description || ""
        })),

        experience: (profileData.experiences || profileData.experience || data.experiences || data.experience || []).map(item => ({
            id: item.id,
            title: item.position || item.title || "",
            company: item.company || "",
            location: item.location || "",
            startDate: item.start_date || item.startDate || "",
            endDate: item.end_date || item.endDate || "",
            description: item.description || ""
        })),

        social_links: (profileData.social_links || data.social_links || []).map(item => ({
            id: item.id,
            platform: item.platform || "",
            address: item.address || item.url || ""
        })),

        languages: (profileData.languages || data.languages || []).map(item => ({
            id: item.id,
            language: item.language || item.lang || item.name || "",
            proficiency: item.proficiency || item.level || ""
        }))
    };
}

class InstructorProfilePage {
    constructor() {
        this.profile = {};
        this.currentModalType = null;
        this.currentEditId = null;
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadProfile();
        this.hideLoader();
    }

    bindEvents() {

        // User menu


        // Cover & Avatar upload
        document.getElementById('coverUploadBtn')?.addEventListener('click', () => {
            document.getElementById('coverFileInput')?.click();
        });
        document.getElementById('coverFileInput')?.addEventListener('change', (e) => {
            if (e.target.files[0]) this.uploadCover(e.target.files[0]);
        });
        document.getElementById('avatarUploadBtn')?.addEventListener('click', () => {
            document.getElementById('avatarFileInput')?.click();
        });
        document.getElementById('avatarFileInput')?.addEventListener('change', (e) => {
            if (e.target.files[0]) this.uploadAvatar(e.target.files[0]);
        });

        // Basic info
        document.getElementById('saveBasicInfo')?.addEventListener('click', () => this.saveBasicInfo());
        document.getElementById('bio')?.addEventListener('input', (e) => {
            document.getElementById('bioCount').textContent = `${e.target.value.length}/2000`;
        });

        // Resume upload
        document.getElementById('resumeInput')?.addEventListener('change', (e) => {
            if (e.target.files[0]) this.uploadResume(e.target.files[0]);
        });

        // Skills
        document.getElementById('addSkillBtn')?.addEventListener('click', () => this.addSkill());
        document.getElementById('skillInput')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.addSkill();
        });

        // Section add buttons
        document.getElementById('addEducationBtn')?.addEventListener('click', () => this.openModal('education'));
        document.getElementById('addExperienceBtn')?.addEventListener('click', () => this.openModal('experience'));
        document.getElementById('addSocialBtn')?.addEventListener('click', () => this.openModal('social'));
        document.getElementById('addLanguageBtn')?.addEventListener('click', () => this.openModal('language'));

        // Modal
        document.getElementById('modalClose')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalCancel')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalSave')?.addEventListener('click', () => this.saveModalItem());
        document.getElementById('itemModal')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });
    }

    // ============================================
    // DATA LOADING
    // ============================================
    async loadProfile() {

        try {
            const response = await auth.authenticatedRequest(baseUrl + "/api/v1/account/instructor/profile/");

            if (response.ok) {
                const data = await response.json();
                this.profile = mapInstructorProfile(data);

            } else {
                console.error('Failed to load profile');
            }
        } catch (error) {
            console.error('Failed to load profile:', error);

        }
        this.renderAll();
    }



    // ============================================
    // RENDER ALL
    // ============================================
    renderAll() {
        const p = this.profile;

        // Cover & Avatar
        if (p.cover_url) {
            document.getElementById('coverImage').src = p.cover_url;
            document.getElementById('previewCover').style.backgroundImage = `url(${p.cover_url})`;
        }
        const avatarUrl = p.avatar_url || `https://ui-avatars.com/api/?name=${p.first_name}+${p.last_name}&background=8B5CF6&color=fff&size=160`;
        document.getElementById('profileAvatar').src = avatarUrl;
        document.getElementById('displayName').textContent = `Dr. ${p.first_name} ${p.last_name}`;

        // Verification Badge
        if (p.is_verified) {
            document.getElementById('verifiedBadge').textContent = '✅ Verified Instructor';
            document.getElementById('verifiedBadge').style.display = 'inline-flex';
        } else {
            document.getElementById('verifiedBadge').style.display = 'none';
        }
        document.getElementById('orgInline').textContent = p.organization || '';

        // Application Status
        this.renderApplicationStatus();

        // Basic Info
        document.getElementById('firstName').value = p.first_name || '';
        document.getElementById('lastName').value = p.last_name || '';
        document.getElementById('email').value = p.email || '';
        document.getElementById('professionalTitle').value = p.professional_title || '';
        document.getElementById('organization').value = p.organization || '';
        document.getElementById('yearsExperience').value = p.years_of_experience || 0;
        document.getElementById('company').value = p.company || '';
        document.getElementById('jobTitle').value = p.job_title || '';
        document.getElementById('country').value = p.country || '';
        document.getElementById('timezone').value = p.timezone || '';
        document.getElementById('language').value = p.language || '';
        document.getElementById('website').value = p.website || '';
        document.getElementById('headline').value = p.headline || '';
        document.getElementById('bio').value = p.biography || '';
        document.getElementById('bioCount').textContent = `${(p.biography || '').length}/2000`;
        document.getElementById('introductionVideo').value = p.introduction_video || '';

        // Resume status
        if (p.resume) {
            document.getElementById('resumeStatus').textContent = 'Resume uploaded';
        }

        // Skills
        this.renderSkills();

        // Lists
        this.renderList('education', p.education || [], 'school', 'degree');
        this.renderList('experience', p.experience || [], 'company', 'title');
        this.renderSocialLinks(p.social_links || []);
        this.renderLanguages(p.languages || []);

        // Verification
        this.renderVerification();

        // Preview
        this.updatePreview();
    }

    renderApplicationStatus() {
        const container = document.getElementById('applicationStatus');
        const status = this.profile.application_status;
        const statusMap = {
            'draft': 'Draft',
            'pending': 'Pending Review',
            'approved': 'Approved',
            'rejected': 'Rejected'
        };

        container.innerHTML = `<span class="status-badge ${status}">${statusMap[status] || status}</span>`;

        if (status === 'rejected' && this.profile.rejection_reason) {
            container.innerHTML += `<div class="rejection-reason">Reason: ${this.profile.rejection_reason}</div>`;
        }
    }

    // ============================================
    // SKILLS
    // ============================================
    renderSkills() {
        const container = document.getElementById('skillsContainer');
        const skills = this.profile.skills || [];

        if (!skills.length) {
            container.innerHTML = '<p class="no-items">No skills added yet.</p>';
            return;
        }

        container.innerHTML = skills.map((s, i) => `
            <span class="skill-tag">${s}
                <button class="skill-tag-remove" data-index="${i}"><i class="fas fa-times"></i></button>
            </span>
        `).join('');

        container.querySelectorAll('.skill-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => this.removeSkill(parseInt(btn.dataset.index)));
        });
    }

    async addSkill() {
        const input = document.getElementById('skillInput');
        const skill = input.value.trim();
        if (!skill) return;
        if ((this.profile.skills || []).includes(skill)) {
            this.showToast('Skill already exists');
            return;
        }
        if ((this.profile.skills || []).length >= 50) {
            this.showToast('Maximum 50 skills');
            return;
        }

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/skills/",
                {
                    method: 'POST',
                    body: JSON.stringify({ name: skill })
                }
            );

            if (response.ok) {
                const data = await response.json();
                this.profile.skills.push(data.name || skill);
                input.value = '';
                this.renderSkills();
                this.updatePreview();
                this.showToast('Skill added');
            } else {
                this.showToast('Failed to add skill');
            }
        } catch (error) {
            console.error('Failed to add skill:', error);
            // Fallback: add locally
            this.profile.skills = [...(this.profile.skills || []), skill];
            input.value = '';
            this.renderSkills();
            this.updatePreview();
            this.showToast('Skill added locally');
        }
    }

    async removeSkill(index) {
        const skillName = this.profile.skills[index];
        if (!skillName) return;

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/skills/delete/",
                {
                    method: 'DELETE',
                    body: JSON.stringify({ name: skillName })
                }
            );

            if (response.ok) {
                this.profile.skills = this.profile.skills.filter(item => item !== skillName);
                this.renderSkills();
                this.updatePreview();
                this.showToast('Skill removed');
            } else {
                this.showToast('Failed to remove skill');
            }
        } catch (error) {
            console.error('Failed to remove skill:', error);
            // Fallback: remove locally
            this.profile.skills.splice(index, 1);
            this.renderSkills();
            this.updatePreview();
            this.showToast('Skill removed locally');
        }
    }

    // ============================================
    // GENERIC LIST (Education, Experience)
    // ============================================
    renderList(type, items, subtitleKey, titleKey) {
        const container = document.getElementById(`${type}List`);

        if (!items || items.length === 0) {
            container.innerHTML = '<p class="no-items">No items yet. Click "+ Add" to get started.</p>';
            return;
        }

        const iconMap = {
            'education': 'fa-graduation-cap',
            'experience': 'fa-briefcase'
        };

        container.innerHTML = items.map(item => `
            <div class="item-card">
                <div class="item-icon"><i class="fas ${iconMap[type]}"></i></div>
                <div class="item-content">
                    <div class="item-title">${item[titleKey] || ''}</div>
                    <div class="item-subtitle">${item[subtitleKey] || ''}${item.field ? ' · ' + item.field : ''}${item.location ? ' · ' + item.location : ''}</div>
                    <div class="item-date">${this.formatDateRange(item.startDate, item.endDate)}</div>
                    ${item.description ? `<div class="item-description">${item.description}</div>` : ''}
                </div>
                <div class="item-actions">
                    <button class="item-action-btn" data-action="edit" data-id="${item.id}" data-type="${type}"><i class="fas fa-pen"></i></button>
                    <button class="item-action-btn delete" data-action="delete" data-id="${item.id}" data-type="${type}"><i class="fas fa-trash-alt"></i></button>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.item-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const id = parseInt(btn.dataset.id);
                const itemType = btn.dataset.type;

                if (action === 'edit') {
                    const item = (this.profile[itemType] || []).find(i => i.id === id);
                    this.openModal(itemType, item);
                } else if (action === 'delete') {
                    this.deleteItem(itemType, id);
                }
            });
        });
    }

    async deleteItem(key, id) {
        const endpointMap = {
            'education': '/api/v1/account/educations/',
            'experience': '/api/v1/account/experiences/',
            'social_links': '/api/v1/account/social-links/',
            'languages': '/api/v1/account/languages/'
        };

        const url = baseUrl + (endpointMap[key] || `/api/v1/account/${key}/`) + id + '/';

        try {
            const response = await auth.authenticatedRequest(url, { method: 'DELETE' });

            if (response.ok) {
                this.profile[key] = (this.profile[key] || []).filter(i => i.id !== id);
                this.rerenderList(key);
                this.updatePreview();
                this.showToast('Item deleted');
            } else {
                this.showToast('Failed to delete item');
            }
        } catch (error) {
            console.error('Failed to delete item:', error);
            // Fallback: delete locally
            this.profile[key] = (this.profile[key] || []).filter(i => i.id !== id);
            this.rerenderList(key);
            this.updatePreview();
            this.showToast('Item deleted locally');
        }
    }

    rerenderList(key) {
        if (key === 'education') {
            this.renderList('education', this.profile.education, 'school', 'degree');
        } else if (key === 'experience') {
            this.renderList('experience', this.profile.experience, 'company', 'title');
        } else if (key === 'social_links') {
            this.renderSocialLinks(this.profile.social_links);
        } else if (key === 'languages') {
            this.renderLanguages(this.profile.languages);
        }
    }

    // ============================================
    // SOCIAL LINKS
    // ============================================
    renderSocialLinks(links) {
        const container = document.getElementById('socialList');

        if (!links || links.length === 0) {
            container.innerHTML = '<p class="no-items">No social links yet.</p>';
            return;
        }

        container.innerHTML = links.map(link => `
            <div class="social-link-item">
                <span class="social-platform-icon ${link.platform}"><i class="fab fa-${link.platform}"></i></span>
                <span class="social-link-url">${link.address}</span>
                <div class="item-actions">
                    <button class="item-action-btn" data-action="edit" data-id="${link.id}" data-type="social"><i class="fas fa-pen"></i></button>
                    <button class="item-action-btn delete" data-action="delete" data-id="${link.id}" data-type="social"><i class="fas fa-trash-alt"></i></button>
                </div>
            </div>
        `).join('');

        this.bindSocialActions();
    }

    bindSocialActions() {
        const container = document.getElementById('socialList');
        container.querySelectorAll('.item-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const id = parseInt(btn.dataset.id);

                if (action === 'edit') {
                    const item = (this.profile.social_links || []).find(i => i.id === id);
                    this.openModal('social', item);
                } else if (action === 'delete') {
                    this.deleteItem('social_links', id);
                }
            });
        });
    }

    // ============================================
    // LANGUAGES
    // ============================================
    renderLanguages(languages) {
        const container = document.getElementById('languagesList');

        if (!languages || languages.length === 0) {
            container.innerHTML = '<p class="no-items">No languages added yet.</p>';
            return;
        }

        container.innerHTML = languages.map(lang => `
            <div class="language-item">
                <span class="language-name">${lang.language}</span>
                <span class="language-level">${lang.proficiency}</span>
                <div class="item-actions">
                    <button class="item-action-btn" data-action="edit" data-id="${lang.id}" data-type="language"><i class="fas fa-pen"></i></button>
                    <button class="item-action-btn delete" data-action="delete" data-id="${lang.id}" data-type="language"><i class="fas fa-trash-alt"></i></button>
                </div>
            </div>
        `).join('');

        this.bindLanguageActions();
    }

    bindLanguageActions() {
        const container = document.getElementById('languagesList');
        container.querySelectorAll('.item-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const id = parseInt(btn.dataset.id);

                if (action === 'edit') {
                    const item = (this.profile.languages || []).find(i => i.id === id);
                    this.openModal('language', item);
                } else if (action === 'delete') {
                    this.deleteItem('languages', id);
                }
            });
        });
    }

    // ============================================
    // VERIFICATION
    // ============================================
    renderVerification() {
        const body = document.getElementById('verificationBody');

        if (this.profile.is_verified) {
            body.innerHTML = `
                <div class="verification-status verified">
                    <i class="fas fa-check-circle" style="color:#059669;font-size:1.5rem;"></i>
                    <div>
                        <strong style="color:#065F46;">Verified Instructor</strong>
                        <p style="font-size:0.8rem;color:#065F46;margin:0;">Your credentials have been verified.</p>
                        ${this.profile.verification_date ? `<p style="font-size:0.7rem;color:#065F46;margin:0;">Verified on: ${new Date(this.profile.verification_date).toLocaleDateString()}</p>` : ''}
                    </div>
                </div>
            `;
        } else if (this.profile.application_status === 'pending') {
            body.innerHTML = `
                <div class="verification-status pending">
                    <i class="fas fa-clock" style="color:#D97706;font-size:1.5rem;"></i>
                    <div>
                        <strong style="color:#92400E;">Verification Pending</strong>
                        <p style="font-size:0.8rem;color:#92400E;margin:0;">Your verification application is under review.</p>
                    </div>
                </div>
            `;
        } else if (this.profile.application_status === 'rejected') {
            body.innerHTML = `
                <div class="verification-status rejected">
                    <i class="fas fa-times-circle" style="color:#DC2626;font-size:1.5rem;"></i>
                    <div>
                        <strong style="color:#991B1B;">Verification Rejected</strong>
                        <p style="font-size:0.8rem;color:#991B1B;margin:0;">${this.profile.rejection_reason || 'Your application was rejected.'}</p>
                    </div>
                </div>
                <button class="verification-btn" id="reapplyVerificationBtn"><i class="fas fa-redo"></i> Reapply for Verification</button>
            `;
            document.getElementById('reapplyVerificationBtn')?.addEventListener('click', () => this.applyForVerification());
        } else {
            body.innerHTML = `
                <div class="verification-status not-applied">
                    <i class="fas fa-shield-halved" style="color:var(--color-gray-400);font-size:1.5rem;"></i>
                    <div>
                        <strong>Not Verified</strong>
                        <p style="font-size:0.8rem;color:var(--color-gray-500);margin:0;">Apply for verification to build trust with students.</p>
                    </div>
                </div>
                <button class="verification-btn" id="applyVerificationBtn"><i class="fas fa-check-circle"></i> Apply for Verification</button>
            `;
            document.getElementById('applyVerificationBtn')?.addEventListener('click', () => this.applyForVerification());
        }
    }

    async applyForVerification() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/instructor/verification/apply/",
                {
                    method: 'POST'
                }
            );

            if (response.ok) {
                this.profile.application_status = 'pending';
                this.renderApplicationStatus();
                this.renderVerification();
                this.showToast('Verification application submitted!');
            } else {
                this.showToast('Failed to submit application');
            }
        } catch (error) {
            console.error('Failed to apply for verification:', error);
            this.showToast('Failed to submit application');
        }
    }

    // ============================================
    // MODAL
    // ============================================
    openModal(type, data = null) {
        this.currentModalType = type;
        this.currentEditId = data?.id || null;

        const modal = document.getElementById('itemModal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');

        const titles = {
            education: 'Education',
            experience: 'Experience',
            social: 'Social Link',
            language: 'Language'
        };

        title.textContent = data ? `Edit ${titles[type]}` : `Add ${titles[type]}`;

        if (type === 'education' || type === 'experience') {
            const isEdu = type === 'education';
            body.innerHTML = `
                <div class="form-group">
                    <label>${isEdu ? 'School' : 'Company'} *</label>
                    <input type="text" id="modalField1" class="form-input" value="${data?.[isEdu ? 'school' : 'company'] || ''}">
                </div>
                <div class="form-group">
                    <label>${isEdu ? 'Degree' : 'Title'} *</label>
                    <input type="text" id="modalField2" class="form-input" value="${data?.[isEdu ? 'degree' : 'title'] || ''}">
                </div>
                ${isEdu ? `
                    <div class="form-group">
                        <label>Field of Study *</label>
                        <input type="text" id="modalField3" class="form-input" value="${data?.field || ''}">
                    </div>
                ` : `
                    <div class="form-group">
                        <label>Location</label>
                        <input type="text" id="modalField3" class="form-input" value="${data?.location || ''}">
                    </div>
                `}
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div class="form-group">
                        <label>Start Date</label>
                        <input type="month" id="modalStartDate" class="form-input" value="${data?.startDate || ''}">
                    </div>
                    <div class="form-group">
                        <label>End Date</label>
                        <input type="month" id="modalEndDate" class="form-input" value="${data?.endDate || ''}">
                    </div>
                </div>
                <label style="display:flex;align-items:center;gap:8px;font-size:0.85rem;cursor:pointer;">
                    <input type="checkbox" id="modalCurrently" ${data && !data.endDate ? 'checked' : ''}>
                    Currently ${isEdu ? 'studying' : 'working'} here
                </label>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="modalDesc" class="form-input form-textarea" rows="3">${data?.description || ''}</textarea>
                </div>
            `;

            document.getElementById('modalCurrently')?.addEventListener('change', (e) => {
                document.getElementById('modalEndDate').disabled = e.target.checked;
                if (e.target.checked) document.getElementById('modalEndDate').value = '';
            });

            if (data && !data.endDate) {
                document.getElementById('modalEndDate').disabled = true;
            }
        } else if (type === 'social') {
            body.innerHTML = `
                <div class="form-group">
                    <label>Platform</label>
                    <select id="modalPlatform" class="form-input">
                        <option value="linkedin" ${data?.platform === 'linkedin' ? 'selected' : ''}>LinkedIn</option>
                        <option value="github" ${data?.platform === 'github' ? 'selected' : ''}>GitHub</option>
                        <option value="twitter" ${data?.platform === 'twitter' ? 'selected' : ''}>Twitter</option>
                        <option value="website" ${data?.platform === 'website' ? 'selected' : ''}>Website</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>URL</label>
                    <input type="url" id="modalUrl" class="form-input" value="${data?.address || ''}" placeholder="https://...">
                </div>
            `;
        } else if (type === 'language') {
            body.innerHTML = `
                <div class="form-group">
                    <label>Language</label>
                    <input type="text" id="modalLanguage" class="form-input" value="${data?.language || ''}" placeholder="e.g. French">
                </div>
                <div class="form-group">
                    <label>Proficiency</label>
                    <select id="modalProficiency" class="form-input">
                        <option value="Native" ${data?.proficiency === 'Native' ? 'selected' : ''}>Native</option>
                        <option value="C2" ${data?.proficiency === 'C2' ? 'selected' : ''}>C2 - Proficient</option>
                        <option value="C1" ${data?.proficiency === 'C1' ? 'selected' : ''}>C1 - Advanced</option>
                        <option value="B2" ${data?.proficiency === 'B2' ? 'selected' : ''}>B2 - Upper Intermediate</option>
                        <option value="B1" ${data?.proficiency === 'B1' ? 'selected' : ''}>B1 - Intermediate</option>
                        <option value="A2" ${data?.proficiency === 'A2' ? 'selected' : ''}>A2 - Elementary</option>
                        <option value="A1" ${data?.proficiency === 'A1' ? 'selected' : ''}>A1 - Beginner</option>
                    </select>
                </div>
            `;
        }

        modal.style.display = 'flex';
    }

    closeModal() {
        document.getElementById('itemModal').style.display = 'none';
        this.currentModalType = null;
        this.currentEditId = null;
    }

    async saveModalItem() {
        const type = this.currentModalType;
        let item = {};
        let url = '';
        let method = 'POST';

        if (type === 'education' || type === 'experience') {
            const isEdu = type === 'education';
            item = {
                [isEdu ? 'institution' : 'company']: document.getElementById('modalField1').value.trim(),
                [isEdu ? 'degree' : 'position']: document.getElementById('modalField2').value.trim(),
                [isEdu ? 'field_of_study' : 'location']: document.getElementById('modalField3').value.trim(),
                start_date: document.getElementById('modalStartDate').value || null,
                end_date: document.getElementById('modalCurrently')?.checked ? null : (document.getElementById('modalEndDate').value || null),
                description: document.getElementById('modalDesc').value.trim()
            };

            if (!item[isEdu ? 'institution' : 'company'] || !item[isEdu ? 'degree' : 'position']) {
                this.showToast('Please fill required fields');
                return;
            }

            const endpointType = type === 'education' ? 'educations' : 'experiences';
            url = baseUrl + `/api/v1/account/${endpointType}/`;
            if (this.currentEditId) {
                url += this.currentEditId + '/';
                method = 'PATCH';
            }
        } else if (type === 'social') {
            item = {
                platform: document.getElementById('modalPlatform').value,
                address: document.getElementById('modalUrl').value.trim()
            };

            if (!item.address) {
                this.showToast('Please enter a URL');
                return;
            }

            url = baseUrl + '/api/v1/account/social-links/';
            if (this.currentEditId) {
                url += this.currentEditId + '/';
                method = 'PATCH';
            }
        } else if (type === 'language') {
            item = {
                language: document.getElementById('modalLanguage').value.trim(),
                proficiency: document.getElementById('modalProficiency').value
            };

            if (!item.language) {
                this.showToast('Please enter a language');
                return;
            }

            url = baseUrl + '/api/v1/account/languages/';
            if (this.currentEditId) {
                url += this.currentEditId + '/';
                method = 'PATCH';
            }
        }

        try {
            const response = await auth.authenticatedRequest(url, {
                method: method,
                body: JSON.stringify(item)
            });

            if (response.ok) {
                await this.loadProfile();
                this.closeModal();
                this.showToast('Saved successfully');
            } else {
                const errorData = await response.json().catch(() => ({}));
                this.showToast(errorData.message || errorData.detail || 'Failed to save');
            }
        } catch (error) {
            console.error('Failed to save:', error);
            // Fallback: save locally without API
            this.saveModalItemLocally(type);
            this.updatePreview();
            this.closeModal();
            this.showToast('Saved locally (offline)');
        }
    }

    saveModalItemLocally(type) {
        let item = { id: this.currentEditId || Date.now() };

        if (type === 'education' || type === 'experience') {
            const isEdu = type === 'education';
            item = {
                ...item,
                [isEdu ? 'school' : 'company']: document.getElementById('modalField1').value.trim(),
                [isEdu ? 'degree' : 'title']: document.getElementById('modalField2').value.trim(),
                [isEdu ? 'field' : 'location']: document.getElementById('modalField3').value.trim(),
                startDate: document.getElementById('modalStartDate').value,
                endDate: document.getElementById('modalCurrently')?.checked ? null : document.getElementById('modalEndDate').value,
                description: document.getElementById('modalDesc').value.trim()
            };

            const key = type === 'education' ? 'education' : 'experience';
            if (this.currentEditId) {
                const idx = this.profile[key].findIndex(i => i.id === this.currentEditId);
                if (idx >= 0) this.profile[key][idx] = item;
            } else {
                this.profile[key] = [...(this.profile[key] || []), item];
            }
            this.renderList(type, this.profile[key], isEdu ? 'school' : 'company', isEdu ? 'degree' : 'title');
        } else if (type === 'social') {
            item = {
                ...item,
                platform: document.getElementById('modalPlatform').value,
                address: document.getElementById('modalUrl').value.trim()
            };

            if (this.currentEditId) {
                const idx = this.profile.social_links.findIndex(i => i.id === this.currentEditId);
                if (idx >= 0) this.profile.social_links[idx] = item;
            } else {
                this.profile.social_links = [...(this.profile.social_links || []), item];
            }
            this.renderSocialLinks(this.profile.social_links);
        } else if (type === 'language') {
            item = {
                ...item,
                language: document.getElementById('modalLanguage').value.trim(),
                proficiency: document.getElementById('modalProficiency').value
            };

            if (this.currentEditId) {
                const idx = this.profile.languages.findIndex(i => i.id === this.currentEditId);
                if (idx >= 0) this.profile.languages[idx] = item;
            } else {
                this.profile.languages = [...(this.profile.languages || []), item];
            }
            this.renderLanguages(this.profile.languages);
        }
    }

    // ============================================
    // BASIC INFO SAVE
    // ============================================
    async saveBasicInfo() {
        this.profile.first_name = document.getElementById('firstName').value.trim();
        this.profile.last_name = document.getElementById('lastName').value.trim();
        this.profile.professional_title = document.getElementById('professionalTitle').value.trim();
        this.profile.organization = document.getElementById('organization').value.trim();
        this.profile.years_of_experience = parseInt(document.getElementById('yearsExperience').value) || 0;
        this.profile.company = document.getElementById('company').value.trim();
        this.profile.job_title = document.getElementById('jobTitle').value.trim();
        this.profile.country = document.getElementById('country').value.trim();
        this.profile.timezone = document.getElementById('timezone').value.trim();
        this.profile.language = document.getElementById('language').value.trim();
        this.profile.website = document.getElementById('website').value.trim();
        this.profile.headline = document.getElementById('headline').value.trim();
        this.profile.biography = document.getElementById('bio').value.trim();
        this.profile.introduction_video = document.getElementById('introductionVideo').value.trim();

        const body = JSON.stringify({
            first_name: this.profile.first_name,
            last_name: this.profile.last_name,
            professional_title: this.profile.professional_title,
            organization: this.profile.organization,
            years_of_experience: this.profile.years_of_experience,
            company: this.profile.company,
            job_title: this.profile.job_title,
            country: this.profile.country,
            timezone: this.profile.timezone,
            language: this.profile.language,
            website: this.profile.website,
            headline: this.profile.headline,
            biography: this.profile.biography,
            introduction_video: this.profile.introduction_video
        });

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/instructor/profile/update/",
                {
                    method: 'PATCH',
                    body: body
                }
            );

            if (response.ok) {
                const data = await response.json();
                this.profile = mapInstructorProfile(data);
                document.getElementById('displayName').textContent = `Dr. ${this.profile.first_name} ${this.profile.last_name}`;
                document.getElementById('orgInline').textContent = this.profile.organization || '';
                this.updatePreview();
                this.showToast('Profile updated successfully');
            } else {
                const errorData = await response.json().catch(() => ({}));
                this.showToast(errorData.message || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Failed to save basic info:', error);
            document.getElementById('displayName').textContent = `Dr. ${this.profile.first_name} ${this.profile.last_name}`;
            document.getElementById('orgInline').textContent = this.profile.organization || '';
            this.updatePreview();
            this.showToast('Profile updated locally');
        }
    }

    // ============================================
    // UPLOADS
    // ============================================
    async uploadAvatar(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/instructor/profile/update/",
                {
                    method: 'PATCH',
                    body: formData
                }
            );

            if (response.ok) {
                const data = await response.json();
                const avatarUrl = data.avatar_url || data.avatar || (data.profile && data.profile.avatar);
                document.getElementById('profileAvatar').src = avatarUrl;
                document.getElementById('previewAvatar').src = avatarUrl;
                this.profile.avatar_url = avatarUrl;
                this.showToast('Avatar updated');
            } else {
                this.showToast('Failed to upload avatar');
            }
        } catch (error) {
            console.error('Failed to upload avatar:', error);
            const url = URL.createObjectURL(file);
            document.getElementById('profileAvatar').src = url;
            document.getElementById('previewAvatar').src = url;
            this.showToast('Avatar preview (upload failed)');
        }
    }

    async uploadCover(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('cover', file);

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/instructor/profile/update/",
                {
                    method: 'PATCH',
                    body: formData
                }
            );

            if (response.ok) {
                const data = await response.json();
                const coverUrl = data.cover_url || data.cover;
                document.getElementById('coverImage').src = coverUrl;
                document.getElementById('previewCover').style.backgroundImage = `url(${coverUrl})`;
                this.profile.cover_url = coverUrl;
                this.showToast('Cover image updated');
            } else {
                this.showToast('Failed to upload cover');
            }
        } catch (error) {
            console.error('Failed to upload cover:', error);
            const url = URL.createObjectURL(file);
            document.getElementById('coverImage').src = url;
            document.getElementById('previewCover').style.backgroundImage = `url(${url})`;
            this.showToast('Cover preview (upload failed)');
        }
    }

    async uploadResume(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('resume', file);

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/instructor/profile/update/",
                {
                    method: 'PATCH',
                    body: formData
                }
            );

            if (response.ok) {
                const data = await response.json();
                this.profile.resume = data.resume || '';
                document.getElementById('resumeStatus').textContent = `Resume uploaded: ${file.name}`;
                this.showToast('Resume uploaded');
            } else {
                this.showToast('Failed to upload resume');
            }
        } catch (error) {
            console.error('Failed to upload resume:', error);
            document.getElementById('resumeStatus').textContent = `Resume selected: ${file.name} (upload failed)`;
            this.showToast('Resume upload failed');
        }
    }

    // ============================================
    // PREVIEW UPDATE
    // ============================================
    updatePreview() {
        const p = this.profile;

        document.getElementById('previewAvatar').src = document.getElementById('profileAvatar').src;
        document.getElementById('previewName').textContent = `Dr. ${p.first_name} ${p.last_name}`;
        document.getElementById('previewHeadline').textContent = p.headline || '';
        document.getElementById('previewProfessionalTitle').textContent = p.professional_title || '';
        document.getElementById('previewVerified').textContent = p.is_verified ? '✅ Verified Instructor' : '';
        document.getElementById('previewOrg').textContent = p.organization || '';
        document.getElementById('previewBio').textContent = p.biography || '';

        document.getElementById('previewSkills').innerHTML = (p.skills || []).map(s =>
            `<span class="preview-skill-tag">${s}</span>`
        ).join('');

        document.getElementById('previewEducation').innerHTML = (p.education || []).map(e =>
            `<p>${e.degree} at ${e.school} · ${this.formatDateRange(e.startDate, e.endDate)}</p>`
        ).join('');

        document.getElementById('previewExperience').innerHTML = (p.experience || []).map(e =>
            `<p>${e.title} at ${e.company} · ${this.formatDateRange(e.startDate, e.endDate)}</p>`
        ).join('');

        document.getElementById('previewLinks').innerHTML = (p.social_links || []).map(l =>
            `<p><i class="fab fa-${l.platform}"></i> <a href="${l.address}" target="_blank">${l.address}</a></p>`
        ).join('');

        document.getElementById('previewLanguages').innerHTML = (p.languages || []).map(l =>
            `<p>${l.language} (${l.proficiency})</p>`
        ).join('');

        const vidBlock = document.getElementById('previewVideoBlock');
        if (p.introduction_video) {
            vidBlock.style.display = 'block';
            document.getElementById('previewVideo').innerHTML =
                `<p style="color:var(--color-primary-600);">🎥 <a href="${p.introduction_video}" target="_blank">Watch Introduction</a></p>`;
        } else {
            vidBlock.style.display = 'none';
        }
    }

    // ============================================
    // UTILITIES
    // ============================================
    formatDateRange(start, end) {
        if (!start && !end) return '';

        const fmt = (d) => {
            if (!d) return 'Present';
            const dateStr = String(d);
            const parts = dateStr.split('-');
            const year = parts[0];
            const month = parts[1] ? new Date(parseInt(year), parseInt(parts[1]) - 1).toLocaleDateString('en-US', { month: 'short' }) : '';
            return month ? `${month} ${year}` : year;
        };

        const endFormatted = end ? fmt(end) : 'Present';
        return `${fmt(start)} - ${endFormatted}`;
    }

    hideLoader() {
        const loader = document.getElementById('loadingOverlay');
        if (loader) loader.classList.add('hidden');
    }

    showToast(msg) {
        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = msg;
        document.getElementById('toastContainer').appendChild(t);
        requestAnimationFrame(() => {
            t.style.opacity = '1';
            t.style.transform = 'translateY(0)';
        });
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateY(10px)';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }
}

let instructorProfilePage;
document.addEventListener('DOMContentLoaded', () => {
    instructorProfilePage = new InstructorProfilePage();
});
