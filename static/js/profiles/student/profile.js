// ============================================
// PROFILE PAGE CONTROLLER
// ============================================
const baseUrl = window.location.origin;

function mapProfile(data) {
  return {
    id: data.id,
    first_name: data.first_name,
    last_name: data.last_name,
    email: data.email,
    headline: data.headline,
    bio: data.bio || data.biography || "",
    website: data.website,
    avatar_url: data.avatar || data.avatar_url || "",
    cover_url: data.cover || data.cover_url || "",
    skills: (data.skills || []).map(item => typeof item === 'string' ? item : item.name),

    education: (data.educations || data.education || []).map(item => ({
      id: item.id,
      school: item.institution || item.school,
      degree: item.degree,
      field: item.field_of_study || item.field,
      startDate: item.start_year || item.startDate || item.start_date,
      endDate: item.end_year || item.endDate || item.end_date,
      description: item.description
    })),

    experience: (data.experiences || data.experience || []).map(item => ({
      id: item.id,
      title: item.position || item.title,
      company: item.company,
      location: item.location,
      startDate: item.start_date || item.startDate,
      endDate: item.end_date || item.endDate,
      description: item.description
    })),

    social_links: (data.social_links || []).map(item => ({
      id: item.id,
      platform: item.platform,
      url: item.url
    })),

    languages: (data.languages || []).map(item => ({
      id: item.id,
      language: item.language || item.lang || item.name,
      proficiency: item.proficiency || item.level
    })),

    learning_goals: data.learning_goals || []
  };
}

class ProfilePage {
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
        // Cover & Avatar upload
        document.getElementById('coverUploadBtn')?.addEventListener('click', () => document.getElementById('coverFileInput')?.click());
        document.getElementById('coverFileInput')?.addEventListener('change', (e) => this.uploadCover(e.target.files[0]));
        document.getElementById('avatarUploadBtn')?.addEventListener('click', () => document.getElementById('avatarFileInput')?.click());
        document.getElementById('avatarFileInput')?.addEventListener('change', (e) => this.uploadAvatar(e.target.files[0]));

        // Basic info
        document.getElementById('saveBasicInfo')?.addEventListener('click', () => this.saveBasicInfo());
        document.getElementById('bio')?.addEventListener('input', (e) => {
            document.getElementById('bioCount').textContent = `${e.target.value.length}/2000`;
        });

        // Skills
        document.getElementById('addSkillBtn')?.addEventListener('click', () => this.addSkill());
        document.getElementById('skillInput')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') this.addSkill(); });

        // Section add buttons
        document.getElementById('addEducationBtn')?.addEventListener('click', () => this.openModal('education'));
        document.getElementById('addExperienceBtn')?.addEventListener('click', () => this.openModal('experience'));
        document.getElementById('addSocialBtn')?.addEventListener('click', () => this.openModal('social'));
        document.getElementById('addLanguageBtn')?.addEventListener('click', () => this.openModal('language'));

        // Modal
        document.getElementById('modalClose')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalCancel')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalSave')?.addEventListener('click', () => this.saveModalItem());
        document.getElementById('itemModal')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) this.closeModal(); });
    }

    // ============================================
    // DATA LOADING
    // ============================================
    async loadProfile() {
        try {
            const response = await auth.authenticatedRequest(baseUrl + "/api/v1/account/profile/");
            const data = await response.json();
            this.profile = mapProfile(data);
            this.renderAll();
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }

    // ============================================
    // RENDER ALL
    // ============================================
    renderAll() {
        const p = this.profile;
        // Cover & Avatar
        if (p.cover_url) document.getElementById('coverImage').src = p.cover_url;
        document.getElementById('profileAvatar').src = p.avatar_url || `https://ui-avatars.com/api/?name=${p.first_name}+${p.last_name}&background=4F46E5&color=fff&size=160`;
        document.getElementById('displayName').textContent = `${p.first_name} ${p.last_name}`;
        document.getElementById('displayEmail').textContent = p.email;

        // Basic Info
        document.getElementById('firstName').value = p.first_name || '';
        document.getElementById('lastName').value = p.last_name || '';
        document.getElementById('headline').value = p.headline || '';
        document.getElementById('bio').value = p.bio || '';
        document.getElementById('bioCount').textContent = `${(p.bio || '').length}/2000`;
        document.getElementById('website').value = p.website || '';

        // Skills
        this.renderSkills();
        // Education
        this.renderList('education', p.education || [], 'school', 'degree');
        // Experience
        this.renderList('experience', p.experience || [], 'company', 'title');
        // Social
        this.renderSocialLinks(p.social_links || []);
        // Languages
        this.renderLanguages(p.languages || []);

        // Preview
        this.updatePreview();
    }

    // ============================================
    // SKILLS
    // ============================================
    renderSkills() {
        const container = document.getElementById('skillsContainer');
        const skills = this.profile.skills || [];
        container.innerHTML = skills.map((s, i) => `
            <span class="skill-tag">${s}<button class="skill-tag-remove" data-index="${i}"><i class="fas fa-times"></i></button></span>
        `).join('');
        container.querySelectorAll('.skill-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => this.removeSkill(parseInt(btn.dataset.index)));
        });
    }

    async addSkill() {
        const input = document.getElementById('skillInput');
        const skill = input.value.trim();
        if (!skill) return;
        if ((this.profile.skills || []).includes(skill)) { this.showToast('Skill already exists'); return; }
        if ((this.profile.skills || []).length >= 50) { this.showToast('Maximum 50 skills'); return; }

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

                this.profile.skills.push(data.name);
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

                this.profile.skills = this.profile.skills.filter(item => item !== skillName)
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
        container.innerHTML = items.map(item => `
            <div class="item-card">
                <div class="item-icon"><i class="fas ${type === 'education' ? 'fa-graduation-cap' : 'fa-briefcase'}"></i></div>
                <div class="item-content">
                    <div class="item-title">${item[titleKey] || ''}</div>
                    <div class="item-subtitle">${item[subtitleKey] || ''}${item.field ? ' · ' + item.field : ''}${item.location ? ' · ' + item.location : ''}</div>
                    <div class="item-date">${this.formatDateRange(item.startDate, item.endDate)}</div>
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

    async deleteItem(type, id) {
        const endpointMap = {
            'education': '/api/v1/account/profile/education/',
            'experience': '/api/v1/account/profile/experience/',
            'social_links': '/api/v1/account/profile/social-links/',
            'languages': '/api/v1/account/profile/languages/'
        };

        const url = baseUrl + (endpointMap[type] || `/api/v1/account/profile/${type}/`) + id + '/';

        try {
            const response = await auth.authenticatedRequest(url, { method: 'DELETE' });
            if (response.ok) {
                this.profile[type] = (this.profile[type] || []).filter(i => i.id !== id);
                if (type === 'education' || type === 'experience') {
                    this.renderList(type, this.profile[type], type === 'education' ? 'school' : 'company', type === 'education' ? 'degree' : 'title');
                } else if (type === 'social_links') {
                    this.renderSocialLinks(this.profile.social_links);
                } else if (type === 'languages') {
                    this.renderLanguages(this.profile.languages);
                }
                this.updatePreview();
                this.showToast('Item deleted');
            } else {
                this.showToast('Failed to delete item');
            }
        } catch (error) {
            console.error('Failed to delete item:', error);
            // Fallback: delete locally
            this.profile[type] = (this.profile[type] || []).filter(i => i.id !== id);
            if (type === 'education' || type === 'experience') {
                this.renderList(type, this.profile[type], type === 'education' ? 'school' : 'company', type === 'education' ? 'degree' : 'title');
            } else if (type === 'social_links') {
                this.renderSocialLinks(this.profile.social_links);
            } else if (type === 'languages') {
                this.renderLanguages(this.profile.languages);
            }
            this.updatePreview();
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
                <span class="social-link-url">${link.url}</span>
                <div class="item-actions">
                    <button class="item-action-btn" data-action="edit" data-id="${link.id}" data-type="social"><i class="fas fa-pen"></i></button>
                    <button class="item-action-btn delete" data-action="delete" data-id="${link.id}" data-type="social"><i class="fas fa-trash-alt"></i></button>
                </div>
            </div>
        `).join('');
        this.bindItemActions('social');
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
        this.bindItemActions('language');
    }

    bindItemActions(type) {
        const containerId = type === 'social' ? 'socialList' : 'languagesList';
        const container = document.getElementById(containerId);
        if (!container) return;

        container.querySelectorAll('.item-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const id = parseInt(btn.dataset.id);
                const dataKey = type === 'social' ? 'social_links' : 'languages';
                if (action === 'edit') {
                    const items = this.profile[dataKey] || [];
                    const item = items.find(i => i.id === id);
                    this.openModal(type, item);
                } else if (action === 'delete') {
                    this.deleteItem(dataKey, id);
                }
            });
        });
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

        const titles = { education: 'Education', experience: 'Experience', social: 'Social Link', language: 'Language' };
        title.textContent = data ? `Edit ${titles[type]}` : `Add ${titles[type]}`;

        if (type === 'education' || type === 'experience') {
            const isEdu = type === 'education';
            body.innerHTML = `
                <div class="form-group"><label>${isEdu ? 'School' : 'Company'} *</label><input type="text" id="modalField1" class="form-input" value="${data?.[isEdu ? 'school' : 'company'] || ''}"></div>
                <div class="form-group"><label>${isEdu ? 'Degree' : 'Title'} *</label><input type="text" id="modalField2" class="form-input" value="${data?.[isEdu ? 'degree' : 'title'] || ''}"></div>
                ${isEdu ? '<div class="form-group"><label>Field of Study</label><input type="text" id="modalField3" class="form-input" value="' + (data?.field || '') + '"></div>' : '<div class="form-group"><label>Location</label><input type="text" id="modalField3" class="form-input" value="' + (data?.location || '') + '"></div>'}
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div class="form-group"><label>Start Date</label><input type="month" id="modalStartDate" class="form-input" value="${data?.startDate || ''}"></div>
                    <div class="form-group"><label>End Date</label><input type="month" id="modalEndDate" class="form-input" value="${data?.endDate || ''}"></div>
                </div>
                <label style="display:flex;align-items:center;gap:8px;font-size:0.85rem;cursor:pointer;"><input type="checkbox" id="modalCurrently" ${data && !data.endDate ? 'checked' : ''}> Currently ${isEdu ? 'studying' : 'working'} here</label>
                <div class="form-group"><label>Description</label><textarea id="modalDesc" class="form-input form-textarea" rows="3">${data?.description || ''}</textarea></div>
            `;
            document.getElementById('modalCurrently')?.addEventListener('change', (e) => {
                document.getElementById('modalEndDate').disabled = e.target.checked;
                if (e.target.checked) document.getElementById('modalEndDate').value = '';
            });
        } else if (type === 'social') {
            body.innerHTML = `
                <div class="form-group"><label>Platform</label><select id="modalPlatform" class="form-input"><option value="linkedin" ${data?.platform === 'linkedin' ? 'selected' : ''}>LinkedIn</option><option value="github" ${data?.platform === 'github' ? 'selected' : ''}>GitHub</option><option value="twitter" ${data?.platform === 'twitter' ? 'selected' : ''}>Twitter</option><option value="website" ${data?.platform === 'website' ? 'selected' : ''}>Website</option></select></div>
                <div class="form-group"><label>URL</label><input type="url" id="modalUrl" class="form-input" value="${data?.url || ''}" placeholder="https://..."></div>
            `;
        } else if (type === 'language') {
            body.innerHTML = `
                <div class="form-group"><label>Language</label><input type="text" id="modalLanguage" class="form-input" value="${data?.language || ''}" placeholder="e.g. French"></div>
                <div class="form-group"><label>Proficiency</label><select id="modalProficiency" class="form-input"><option value="Native" ${data?.proficiency === 'Native' ? 'selected' : ''}>Native</option><option value="C2" ${data?.proficiency === 'C2' ? 'selected' : ''}>C2 - Proficient</option><option value="C1" ${data?.proficiency === 'C1' ? 'selected' : ''}>C1 - Advanced</option><option value="B2" ${data?.proficiency === 'B2' ? 'selected' : ''}>B2 - Upper Intermediate</option><option value="B1" ${data?.proficiency === 'B1' ? 'selected' : ''}>B1 - Intermediate</option><option value="A2" ${data?.proficiency === 'A2' ? 'selected' : ''}>A2 - Elementary</option><option value="A1" ${data?.proficiency === 'A1' ? 'selected' : ''}>A1 - Beginner</option></select></div>
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

            const endpointType = type === 'education' ? 'education' : 'experience';
            url = baseUrl + `/api/v1/account/profile/${endpointType}/`;
            if (this.currentEditId) {
                url += this.currentEditId + '/';
                method = 'PATCH';
            }
        } else if (type === 'social') {
            item = {
                platform: document.getElementById('modalPlatform').value,
                url: document.getElementById('modalUrl').value.trim()
            };
            if (!item.url) { this.showToast('Please enter a URL'); return; }

            url = baseUrl + '/api/v1/account/profile/social-links/';
            if (this.currentEditId) {
                url += this.currentEditId + '/';
                method = 'PATCH';
            }
        } else if (type === 'language') {
            item = {
                language: document.getElementById('modalLanguage').value.trim(),
                proficiency: document.getElementById('modalProficiency').value
            };
            if (!item.language) { this.showToast('Please enter a language'); return; }

            url = baseUrl + '/api/v1/account/profile/languages/';
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
                // Reload profile to get fresh data from server
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

            if (this.currentEditId) {
                const idx = this.profile[type].findIndex(i => i.id === this.currentEditId);
                if (idx >= 0) this.profile[type][idx] = item;
            } else {
                this.profile[type] = [...(this.profile[type] || []), item];
            }
            this.renderList(type, this.profile[type], isEdu ? 'school' : 'company', isEdu ? 'degree' : 'title');
        } else if (type === 'social') {
            item = {
                ...item,
                platform: document.getElementById('modalPlatform').value,
                url: document.getElementById('modalUrl').value.trim()
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
        this.profile.headline = document.getElementById('headline').value.trim();
        this.profile.bio = document.getElementById('bio').value.trim();
        this.profile.website = document.getElementById('website').value.trim();

        const body = JSON.stringify({
            first_name: this.profile.first_name,
            last_name: this.profile.last_name,
            headline: this.profile.headline,
            biography: this.profile.bio,
            website: this.profile.website,
        });

        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/basic-info/update/",
                {
                    method: 'PATCH',
                    body: body
                }
            );

            if (response.ok) {
                const data = await response.json();
                this.profile = mapProfile(data);
                document.getElementById('displayName').textContent = `${this.profile.first_name} ${this.profile.last_name}`;
                this.updatePreview();
                this.showToast('Profile updated successfully');
            } else {
                this.showToast('Failed to update profile');
            }
        } catch (error) {
            console.error('Failed to save basic info:', error);
            document.getElementById('displayName').textContent = `${this.profile.first_name} ${this.profile.last_name}`;
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
                baseUrl + "/api/v1/account/profile/avatar/",
                {
                    method: 'POST',
                    body: formData
                    // Note: Do NOT set Content-Type header for FormData
                }
            );

            if (response.ok) {
                const data = await response.json();
                const avatarUrl = data.avatar_url || data.avatar;
                document.getElementById('profileAvatar').src = avatarUrl;
                document.getElementById('previewAvatar').src = avatarUrl;
                this.profile.avatar_url = avatarUrl;
                this.showToast('Avatar updated');
            } else {
                this.showToast('Failed to upload avatar');
            }
        } catch (error) {
            console.error('Failed to upload avatar:', error);
            // Fallback: show locally
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
                baseUrl + "/api/v1/account/profile/cover/",
                {
                    method: 'POST',
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

    // ============================================
    // PREVIEW UPDATE
    // ============================================
    updatePreview() {
        const p = this.profile;
        document.getElementById('previewAvatar').src = document.getElementById('profileAvatar').src;
        document.getElementById('previewName').textContent = `${p.first_name} ${p.last_name}`;
        document.getElementById('previewHeadline').textContent = p.headline || '';
        document.getElementById('previewBio').textContent = p.bio || '';

        document.getElementById('previewSkills').innerHTML = (p.skills || []).map(s => `<span class="preview-skill-tag">${s}</span>`).join('');
        document.getElementById('previewEducation').innerHTML = (p.education || []).map(e => `<p>${e.degree} at ${e.school} · ${this.formatDateRange(e.startDate, e.endDate)}</p>`).join('');
        document.getElementById('previewExperience').innerHTML = (p.experience || []).map(e => `<p>${e.title} at ${e.company} · ${this.formatDateRange(e.startDate, e.endDate)}</p>`).join('');
        document.getElementById('previewLinks').innerHTML = (p.social_links || []).map(l => `<p><i class="fab fa-${l.platform}"></i> <a href="${l.url}" target="_blank">${l.url}</a></p>`).join('');
        document.getElementById('previewLanguages').innerHTML = (p.languages || []).map(l => `<p>${l.language} (${l.proficiency})</p>`).join('');
    }

    // ============================================
    // UTILITIES
    // ============================================
    formatDateRange(start, end) {
        const fmt = (d) => {
            if (!d) return 'Present';
            const dateStr = String(d);
            // Handle both "YYYY-MM" and "YYYY-MM-DD" formats
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

let profilePage;
document.addEventListener('DOMContentLoaded', () => { profilePage = new ProfilePage(); });
