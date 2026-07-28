// ============================================
// CREATE COURSE PAGE CONTROLLER
// ============================================
const baseUrl = window.location.origin;

function buildFormData(data, formData = new FormData(), parentKey = '') {

    if (data === null || data === undefined) {
        return formData;
    }

    // Handle Files and Blobs
    if (data instanceof File || data instanceof Blob) {
        formData.append(parentKey, data);
        return formData;
    }

    // Handle Arrays
    if (Array.isArray(data)) {
        data.forEach((item, index) => {
            const key = parentKey ? `${parentKey}[${index}]` : `${index}`;
            if (typeof item === 'object' && item !== null && !(item instanceof File)) {
                buildFormData(item, formData, key);
            } else {
                formData.append(key, item);
            }
        });
        return formData;
    }

    // Handle Objects
    if (typeof data === 'object') {
        Object.keys(data).forEach(key => {
            const value = data[key];
            const newKey = parentKey ? `${parentKey}.${key}` : key;

            // Handle special cases for file fields
            if (key === 'thumbnail' || key === 'promoVideo' || key === 'courseTrailer') {
                if (value instanceof File) {
                    formData.append(newKey, value);
                }
                // If it's a URL string or null, send as string
                else if (typeof value === 'string' || value === null) {
                    formData.append(newKey, value || '');
                }
                return;
            }

            // Handle file arrays like attachment_files, caption_files, etc.
            if (key === 'attachment_files' || key === 'caption_files' || key === 'pdf_files' || key === 'video_files') {
                if (Array.isArray(value)) {
                    value.forEach((file, index) => {
                        if (file instanceof File) {
                            formData.append(`${newKey}[${index}]`, file);
                        }
                    });
                } else if (value instanceof File) {
                    formData.append(newKey, value);
                }
                return;
            }

            if (value instanceof Date) {
                formData.append(newKey, value.toISOString());
                return;
            }

            if (typeof value === 'object' && value !== null && !(value instanceof File)) {
                buildFormData(value, formData, newKey);
            } else {
                formData.append(newKey, value);
            }
        });
        return formData;
    }

    // Primitive values
    if (parentKey) {
        formData.append(parentKey, data);
    }
    return formData;
}

function mapData(courseData){
    console.log("map data input(coursedata):",courseData)
    const { shortDescription, promoVideo, courseTrailer, priceType, discountPrice, fullDescription, thumbnailPreview, versionNotes, ...rest } = courseData;
    const payload = {
        ...rest,
        short_description: shortDescription,
        promo_video: promoVideo,
        course_trailer: courseTrailer,
        price_type: priceType,
        price_discount: discountPrice,
        description: fullDescription,
        version_note: versionNotes
    }
    console.log(payload)
    return payload
}

class CreateCoursePage {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 8;
        this.courseData = this.getDefaultData();
        this.autoSaveTimer = null;
        this.editingLesson = null;
        this.dragState = {
            active: false,
            type: null,
            sourceSection: null,
            sourceLesson: null,
            sourceIndex: null,
            element: null,
            clone: null,
            startX: 0,
            startY: 0,
            offsetX: 0,
            offsetY: 0
        };
        this.init();
    }

    getDefaultData() {
        return {
            title: '', subtitle: '', shortDescription: '', category: '', subcategory: '', tags: [],
            level: 'intermediate', language: 'en', duration: '', visibility: 'public', fullDescription: '',
            sections: [
                {
                    id: 1, title: 'Introduction', description: '', duration: '', lessons: [
                        {
                            id: 101, title: 'Welcome & Overview', description: '', duration: '', type: 'video',
                            preview: true, published: true, completionRule: 'watch90',
                            content: {
                                videoSource: 'file', videoUrl: '', videoFile: null, videoFileName: '',
                                textContent: '', transcript: '',
                                captions: [],
                                attachments: [],
                                attachment_files: []
                            }
                        },
                        {
                            id: 102, title: 'Course Objectives', description: '', duration: '', type: 'article',
                            preview: true, published: true, completionRule: 'scroll',
                            content: {
                                text: '',
                                attachments: [],
                                attachment_files: []
                            }
                        }
                    ]
                }
            ],
            outcomes: ['Understand core concepts', 'Build real-world projects', 'Master advanced techniques'],
            prerequisites: ['Basic Python knowledge', 'Familiarity with HTML'],
            targetAudience: ['Beginners', 'Software Engineers', 'Students'],
            priceType: 'paid', price: 49.99, discountPrice: '',
            thumbnail: null, promoVideo: '', attachments: [], attachment_files: [], courseTrailer: '',
            seoTitle: '', seoDescription: '',
            version: '1.0', versionNotes: '', versionHistory: [],
            status: 'draft', reviewStatus: 'not_submitted', lastUpdated: new Date()
        };
    }

    async init() {
        this.bindGlobalEvents();
        this.loadDraft();
        this.renderStep(this.currentStep);
        this.startAutoSave();
        this.hideLoader();
    }

    bindGlobalEvents() {
        // UI events
        document.getElementById('hamburgerBtn')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.toggle('open'));
        document.getElementById('mobileMenuBtn')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('appSidebar')?.classList.toggle('open'); });
        document.getElementById('sidebarOverlay')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.remove('open'));
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => { e.stopPropagation(); document.getElementById('userDropdown')?.classList.toggle('open'); });
        document.addEventListener('click', (e) => { if (!e.target.closest('.user-menu-wrapper')) document.getElementById('userDropdown')?.classList.remove('open'); });

        // Navigation
        document.getElementById('prevStepBtn')?.addEventListener('click', () => this.prevStep());
        document.getElementById('nextStepBtn')?.addEventListener('click', () => this.nextStep());
        document.getElementById('saveDraftBtn')?.addEventListener('click', () => this.saveDraft(true));

        // Progress steps
        document.querySelectorAll('.progress-step').forEach(step => {
            step.addEventListener('click', () => {
                const s = parseInt(step.dataset.step);
                this.goToStep(s);
            });
        });

        // Modal
        document.getElementById('lessonModalClose')?.addEventListener('click', () => this.closeLessonModal());
        document.getElementById('lessonModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeLessonModal();
        });
        document.getElementById('lessonModalSave')?.addEventListener('click', () => this.saveLessonContent());
        document.getElementById('lessonModalCancel')?.addEventListener('click', () => this.closeLessonModal());

        // Global drag events (always active, delegated)
        document.addEventListener('mousemove', (e) => this._onMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onMouseUp(e));

        // Touch events for mobile
        document.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
        document.addEventListener('touchend', (e) => this._onTouchEnd(e));

        // CRITICAL FIX: Use event delegation on stepContent for ALL drag handles
        // This ensures drag works even after re-rendering
        const stepContent = document.getElementById('stepContent');
        if (stepContent) {
            stepContent.addEventListener('mousedown', (e) => {
                const handle = e.target.closest('.drag-handle');
                if (!handle) return;

                e.preventDefault();
                e.stopPropagation();

                const dragType = handle.dataset.dragType;

                if (dragType === 'section') {
                    const sectionBlock = handle.closest('.section-block');
                    if (sectionBlock) {
                        const sectionIndex = parseInt(sectionBlock.dataset.section);
                        this._startDrag(e, handle, 'section', { sourceSection: sectionIndex }, sectionBlock);
                    }
                } else if (dragType === 'lesson') {
                    const lessonItem = handle.closest('.lesson-item');
                    if (lessonItem) {
                        const sectionIndex = parseInt(lessonItem.dataset.section);
                        const lessonIndex = parseInt(lessonItem.dataset.lesson);
                        this._startDrag(e, handle, 'lesson', { sourceSection: sectionIndex, sourceLesson: lessonIndex }, lessonItem);
                    }
                } else if (dragType === 'prerequisite') {
                    const prereqItem = handle.closest('.prereq-item');
                    if (prereqItem) {
                        const index = parseInt(prereqItem.dataset.index);
                        this._startDrag(e, handle, 'prerequisites', { sourceIndex: index }, prereqItem);
                    }
                } else if (dragType === 'audience') {
                    const audienceItem = handle.closest('.audience-item');
                    if (audienceItem) {
                        const index = parseInt(audienceItem.dataset.index);
                        this._startDrag(e, handle, 'targetAudience', { sourceIndex: index }, audienceItem);
                    }
                }
            });

            // Touch start for mobile
            stepContent.addEventListener('touchstart', (e) => {
                const handle = e.target.closest('.drag-handle');
                if (!handle) return;

                e.preventDefault();

                const dragType = handle.dataset.dragType;
                const touch = e.touches[0];

                if (dragType === 'prerequisite') {
                    const prereqItem = handle.closest('.prereq-item');
                    if (prereqItem) {
                        const index = parseInt(prereqItem.dataset.index);
                        this._startDrag(touch, handle, 'prerequisites', { sourceIndex: index }, prereqItem);
                    }
                } else if (dragType === 'audience') {
                    const audienceItem = handle.closest('.audience-item');
                    if (audienceItem) {
                        const index = parseInt(audienceItem.dataset.index);
                        this._startDrag(touch, handle, 'targetAudience', { sourceIndex: index }, audienceItem);
                    }
                } else if (dragType === 'section') {
                    const sectionBlock = handle.closest('.section-block');
                    if (sectionBlock) {
                        const sectionIndex = parseInt(sectionBlock.dataset.section);
                        this._startDrag(touch, handle, 'section', { sourceSection: sectionIndex }, sectionBlock);
                    }
                } else if (dragType === 'lesson') {
                    const lessonItem = handle.closest('.lesson-item');
                    if (lessonItem) {
                        const sectionIndex = parseInt(lessonItem.dataset.section);
                        const lessonIndex = parseInt(lessonItem.dataset.lesson);
                        this._startDrag(touch, handle, 'lesson', { sourceSection: sectionIndex, sourceLesson: lessonIndex }, lessonItem);
                    }
                }
            }, { passive: false });
        }
    }

    // ============================================
    // STEP RENDERING
    // ============================================
    renderStep(step) {
        this.currentStep = step;
        this.collectStepData();
        this.updateProgressUI();
        this.updateNavigationButtons();

        const container = document.getElementById('stepContent');
        if (!container) return;

        switch (step) {
            case 1: container.innerHTML = this.renderBasicInfo(); break;
            case 2: container.innerHTML = this.renderCurriculum(); break;
            case 3: container.innerHTML = this.renderOutcomes(); break;
            case 4: container.innerHTML = this.renderPrerequisites(); break;
            case 5: container.innerHTML = this.renderTargetAudience(); break;
            case 6: container.innerHTML = this.renderPricing(); break;
            case 7: container.innerHTML = this.renderMedia(); break;
            case 8: container.innerHTML = this.renderPublishing(); break;
        }

        this.bindStepEvents(step);
        document.getElementById('stepContent').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // STEP 1: Basic Information
    renderBasicInfo() {
        const d = this.courseData;
        return `
            <h2>Basic Information</h2><p class="step-description">Tell students what your course is about</p>
            <div class="form-group"><label>Course Title <span class="required">*</span></label><input type="text" id="courseTitle" class="form-input" value="${this.esc(d.title)}" placeholder="e.g. Complete Python Bootcamp 2026"></div>
            <div class="form-group"><label>Subtitle</label><input type="text" id="courseSubtitle" class="form-input" value="${this.esc(d.subtitle)}" placeholder="A catchy subtitle for your course"></div>
            <div class="form-group"><label>Short Description <span class="required">*</span></label><input type="text" id="shortDesc" class="form-input" value="${this.esc(d.shortDescription)}" placeholder="A concise summary" maxlength="300"><span class="char-count" id="shortDescCount">${(d.shortDescription||'').length}/300</span></div>
            <div class="form-row">
                <div class="form-group"><label>Category <span class="required">*</span></label><select id="courseCategory" class="form-select"><option value="">Select category</option><option value="data-science" ${d.category==='data-science'?'selected':''}>Data Science</option><option value="machine-learning" ${d.category==='machine-learning'?'selected':''}>Machine Learning</option><option value="web-development" ${d.category==='web-development'?'selected':''}>Web Development</option><option value="cloud" ${d.category==='cloud'?'selected':''}>Cloud Computing</option><option value="mobile" ${d.category==='mobile'?'selected':''}>Mobile Development</option></select></div>
                <div class="form-group"><label>Subcategory</label><select id="courseSubcategory" class="form-select"><option value="">Select subcategory</option><option value="python" ${d.subcategory==='python'?'selected':''}>Python</option><option value="javascript" ${d.subcategory==='javascript'?'selected':''}>JavaScript</option><option value="django" ${d.subcategory==='django'?'selected':''}>Django</option><option value="react" ${d.subcategory==='react'?'selected':''}>React</option></select></div>
            </div>
            <div class="form-group"><label>Tags</label><div class="tags-container" id="tagsContainer">${(d.tags||[]).map((t,i)=>`<span class="tag-chip">${this.esc(t)}<button class="tag-chip-remove" data-index="${i}"><i class="fas fa-times"></i></button></span>`).join('')}</div><div class="add-tag-row"><input type="text" id="tagInput" class="form-input" placeholder="Add a tag..."><button class="add-btn" id="addTagBtn"><i class="fas fa-plus"></i> Add</button></div></div>
            <div class="form-row-3">
                <div class="form-group"><label>Level <span class="required">*</span></label><select id="courseLevel" class="form-select"><option value="beginner" ${d.level==='beginner'?'selected':''}>Beginner</option><option value="intermediate" ${d.level==='intermediate'?'selected':''}>Intermediate</option><option value="advanced" ${d.level==='advanced'?'selected':''}>Advanced</option></select></div>
                <div class="form-group"><label>Language <span class="required">*</span></label><select id="courseLanguage" class="form-select"><option value="en" ${d.language==='en'?'selected':''}>English</option><option value="es" ${d.language==='es'?'selected':''}>Español</option><option value="fr" ${d.language==='fr'?'selected':''}>Français</option><option value="de" ${d.language==='de'?'selected':''}>Deutsch</option></select></div>
                <div class="form-group"><label>Duration (hours)</label><input type="text" id="courseDuration" class="form-input" value="${this.esc(d.duration)}" placeholder="e.g. 42"></div>
            </div>
            <div class="form-row"><div class="form-group"><label>Visibility</label><select id="courseVisibility" class="form-select"><option value="public" ${d.visibility==='public'?'selected':''}>Public</option><option value="private" ${d.visibility==='private'?'selected':''}>Private</option><option value="unlisted" ${d.visibility==='unlisted'?'selected':''}>Unlisted</option></select></div></div>
            <div class="form-group"><label>Full Description</label><textarea id="fullDescription" class="form-input form-textarea" placeholder="Describe your course in detail...">${this.esc(d.fullDescription)}</textarea></div>
        `;
    }

    // STEP 2: Curriculum Builder
    renderCurriculum() {
        let html = '<h2>Curriculum Builder</h2><p class="step-description">Organize your course content. Drag to reorder. Click a lesson to add content.</p><div class="curriculum-builder" id="curriculumBuilder">';
        this.courseData.sections.forEach((section, si) => {
            const lessonCount = section.lessons.length;
            html += `
                <div class="section-block" data-section="${si}">
                    <div class="section-header" onclick="createCoursePage.toggleSectionCollapse(${si})">
                        <span class="section-drag drag-handle" data-drag-type="section" data-section="${si}"><i class="fas fa-grip-vertical"></i></span>
                        <div class="section-header-info">
                            <input type="text" value="${this.esc(section.title)}" class="section-title-input" data-section="${si}" placeholder="Section title" onclick="event.stopPropagation();">
                            <div class="section-meta-row">
                                <input type="text" value="${this.esc(section.description||'')}" class="section-meta-input" placeholder="Description" onclick="event.stopPropagation();" style="width:200px;">
                                <input type="text" value="${this.esc(section.duration||'')}" class="section-meta-input" placeholder="Duration" onclick="event.stopPropagation();">
                            </div>
                        </div>
                        <div class="section-actions">
                            <span style="font-size:0.72rem;color:var(--color-gray-400);">${lessonCount} lessons</span>
                            <i class="fas fa-chevron-down collapse-icon" id="collapseIcon${si}"></i>
                            <button class="section-action-btn" onclick="event.stopPropagation();createCoursePage.duplicateSection(${si})" title="Duplicate"><i class="fas fa-copy"></i></button>
                            <button class="section-action-btn delete" onclick="event.stopPropagation();createCoursePage.removeSection(${si})" title="Delete"><i class="fas fa-trash-alt"></i></button>
                        </div>
                    </div>
                    <div class="section-lessons" id="sectionLessons${si}" data-section="${si}">
                        ${section.lessons.map((lesson, li) => this.renderLessonItem(lesson, si, li)).join('')}
                        <button class="add-lesson-btn" data-section="${si}" onclick="event.stopPropagation();createCoursePage.addLesson(${si})"><i class="fas fa-plus"></i> Add Lesson</button>
                    </div>
                </div>`;
        });
        html += '</div><button class="add-section-btn" id="addSectionBtn"><i class="fas fa-plus"></i> Add Section</button>';
        return html;
    }

    renderLessonItem(lesson, si, li) {
        const hasContent = lesson.type === 'video' ? !!(lesson.content?.videoUrl || lesson.content?.videoFile || lesson.content?.textContent) :
                         lesson.type === 'article' ? !!lesson.content?.text :
                         lesson.type === 'pdf' ? !!(lesson.content?.fileUrl || lesson.content?.pdfFile) :
                         lesson.type === 'quiz' ? !!(lesson.content?.questions?.length) :
                         lesson.type === 'assignment' ? !!lesson.content?.description :
                         lesson.type === 'external' ? !!lesson.content?.url : false;
        const typeLabels = { video: 'Video', article: 'Article', pdf: 'PDF', quiz: 'Quiz', assignment: 'Assignment', external: 'External', live_session: 'Live (Soon)', coding_exercise: 'Code (Soon)' };
        const typeOptions = ['video', 'article', 'pdf', 'quiz', 'assignment', 'external', 'live_session', 'coding_exercise'];
        const hasAttachments = (lesson.content?.attachments?.length > 0);
        const hasCaptions = (lesson.content?.captions?.length > 0);
        return `
            <div class="lesson-item" data-section="${si}" data-lesson="${li}">
                <span class="lesson-drag drag-handle" data-drag-type="lesson" data-section="${si}" data-lesson="${li}"><i class="fas fa-grip-vertical"></i></span>
                <span class="lesson-type-icon ${lesson.type}"><i class="fas fa-${lesson.type==='video'?'play':lesson.type==='article'||lesson.type==='pdf'?'file-lines':lesson.type==='quiz'?'circle-question':lesson.type==='assignment'?'tasks':lesson.type==='external'?'link':'code'}"></i></span>
                <span class="lesson-title-display" data-section="${si}" data-lesson="${li}">${this.esc(lesson.title)}</span>
                <i class="fas ${hasContent?'fa-check-circle lesson-content-indicator has-content':'fa-circle lesson-content-indicator no-content'}"></i>
                ${hasAttachments ? '<i class="fas fa-paperclip" style="color:var(--color-gray-400);font-size:0.7rem;" title="Has attachments"></i>' : ''}
                ${hasCaptions ? '<i class="fas fa-closed-captioning" style="color:var(--color-gray-400);font-size:0.7rem;margin-left:2px;" title="Has captions"></i>' : ''}
                <span class="lesson-preview-badge ${lesson.preview?'preview-enabled':'preview-disabled'}">${lesson.preview?'Preview':'No Preview'}</span>
                <span class="lesson-published-badge ${lesson.published?'published':'unpublished'}">${lesson.published?'Pub':'Unpub'}</span>
                <select class="lesson-type-select" data-section="${si}" data-lesson="${li}" onchange="event.stopPropagation();createCoursePage.changeLessonType(${si},${li},this.value)">
                    ${typeOptions.map(t => `<option value="${t}" ${lesson.type===t?'selected':''} ${t==='live_session'||t==='coding_exercise'?'disabled':''}>${typeLabels[t]}</option>`).join('')}
                </select>
                <span class="lesson-item-actions">
                    <button class="lesson-edit-btn" data-section="${si}" data-lesson="${li}" title="Edit content" onclick="event.stopPropagation();createCoursePage.openLessonModal(${si},${li})"><i class="fas fa-pen"></i></button>
                    <button class="section-action-btn" onclick="event.stopPropagation();createCoursePage.duplicateLesson(${si},${li})" title="Duplicate"><i class="fas fa-copy"></i></button>
                    <button class="section-action-btn delete" data-section="${si}" data-lesson="${li}" title="Delete" onclick="event.stopPropagation();createCoursePage.removeLesson(${si},${li})"><i class="fas fa-times"></i></button>
                </span>
            </div>`;
    }

    // STEP 3: Outcomes
    renderOutcomes() {
        return `<h2>Learning Outcomes</h2><p class="step-description">What will students learn from your course?</p><div class="outcomes-list" id="outcomesList">${this.courseData.outcomes.map((o,i)=>`<div class="outcome-item"><i class="fas fa-check-circle"></i><span>${this.esc(o)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newOutcome" class="form-input" placeholder="Add a learning outcome..."><button class="add-btn" id="addOutcomeBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    // STEP 4: Prerequisites
    renderPrerequisites() {
        return `<h2>Prerequisites</h2><p class="step-description">What should students know before taking this course? Drag to reorder.</p><div class="prereq-list" id="prereqList">${this.courseData.prerequisites.map((p,i)=>`<div class="prereq-item" data-index="${i}"><span class="drag-handle" data-drag-type="prerequisite" data-index="${i}"><i class="fas fa-grip-vertical"></i></span><span>${this.esc(p)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newPrereq" class="form-input" placeholder="Add a prerequisite..."><button class="add-btn" id="addPrereqBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    // STEP 5: Target Audience
    renderTargetAudience() {
        return `<h2>Target Audience</h2><p class="step-description">Who is this course for? Drag to reorder.</p><div class="audience-list" id="audienceList">${this.courseData.targetAudience.map((a,i)=>`<div class="audience-item" data-index="${i}"><span class="drag-handle" data-drag-type="audience" data-index="${i}"><i class="fas fa-grip-vertical"></i></span><span>${this.esc(a)}</span><button class="outcome-remove" data-index="${i}"><i class="fas fa-times"></i></button></div>`).join('')}</div><div class="add-tag-row"><input type="text" id="newAudience" class="form-input" placeholder="Add target audience..."><button class="add-btn" id="addAudienceBtn"><i class="fas fa-plus"></i> Add</button></div>`;
    }

    // STEP 6: Pricing
    renderPricing() {
        const d = this.courseData;
        return `<h2>Pricing</h2><p class="step-description">Set the price for your course</p><div class="pricing-toggle" id="pricingToggle"><button class="pricing-option ${d.priceType==='free'?'active':''}" data-type="free">Free</button><button class="pricing-option ${d.priceType==='paid'?'active':''}" data-type="paid">Paid</button></div><div id="pricingFields" style="${d.priceType==='free'?'display:none;':''}"><div class="form-row"><div class="form-group"><label>Price (USD) <span class="required">*</span></label><input type="number" id="coursePrice" class="form-input" value="${d.price||''}" placeholder="49.99" step="0.01" min="0"></div><div class="form-group"><label>Discount Price (optional)</label><input type="number" id="discountPrice" class="form-input" value="${d.discountPrice||''}" placeholder="39.99" step="0.01" min="0"></div></div></div>`;
    }

    // STEP 7: Media & SEO
    renderMedia() {
        const d = this.courseData;
        return `<h2>Media & SEO</h2><p class="step-description">Upload a thumbnail, trailer, and optimize for search engines</p>
            <div class="form-group"><label>Course Thumbnail</label><div class="thumbnail-upload ${d.thumbnailPreview?'has-image':''}" id="thumbnailUpload" onclick="document.getElementById('thumbnailInput').click()">${d.thumbnailPreview ? `<img src="${d.thumbnailPreview}" alt="Thumbnail preview">` : '<div class="upload-placeholder"><i class="fas fa-image"></i><p>Click to upload thumbnail</p><small>Recommended: 1280x720px · Max 2MB</small></div>'}</div><input type="file" id="thumbnailInput" accept="image/*" style="display:none;" onchange="createCoursePage.handleThumbnail(this.files[0])"></div>
            <div class="form-group"><label>Course Trailer URL</label><input type="url" id="courseTrailer" class="form-input" value="${this.esc(d.courseTrailer)}" placeholder="https://youtube.com/watch?v=..."></div>
            <div class="form-group"><label>Promo Video URL</label><input type="url" id="promoVideo" class="form-input" value="${this.esc(d.promoVideo)}" placeholder="https://youtube.com/watch?v=..."></div>
            <div class="form-group"><label>Course Attachments</label><div id="attachmentsList">${(d.attachments||[]).map((a,i)=>`<div class="prereq-item"><i class="fas fa-paperclip"></i><span>${this.esc(a.name||a)}</span><button class="outcome-remove" data-index="${i}" data-type="attachment"><i class="fas fa-times"></i></button></div>`).join('')}${(d.attachments||[]).length===0?'<p style="color:var(--color-gray-400);font-size:0.78rem;text-align:center;padding:8px;">No attachments</p>':''}</div><button class="add-btn" id="addAttachmentBtn"><i class="fas fa-plus"></i> Add Attachment</button><input type="file" id="attachmentInput" style="display:none;" multiple></div>
            <div class="form-row"><div class="form-group"><label>SEO Title</label><input type="text" id="seoTitle" class="form-input" value="${this.esc(d.seoTitle)}" placeholder="Course title for search engines" maxlength="70"></div><div class="form-group"><label>SEO Description</label><input type="text" id="seoDescription" class="form-input" value="${this.esc(d.seoDescription)}" placeholder="Meta description" maxlength="160"></div></div>`;
    }

    // STEP 8: Publishing
    renderPublishing() {
        const checks = [
            { key: 'title', label: 'Course title added', done: !!this.courseData.title },
            { key: 'description', label: 'Description completed', done: !!this.courseData.shortDescription },
            { key: 'thumbnail', label: 'Thumbnail uploaded', done: !!this.courseData.thumbnail },
            { key: 'instructor', label: 'Instructor profile verified', done: true },
            { key: 'category', label: 'Category selected', done: !!this.courseData.category },
            { key: 'outcomes', label: 'Learning outcomes defined', done: this.courseData.outcomes.length > 0 },
            { key: 'language', label: 'Language set', done: !!this.courseData.language },
            { key: 'pricing', label: 'Pricing configured', done: !!(this.courseData.priceType === 'free' || this.courseData.price) },
            { key: 'lessons', label: 'At least 1 published lesson', done: this.courseData.sections.some(s => s.lessons.some(l => l.published)) },
            { key: 'review', label: 'Review passed', done: false }
        ];
        const allDone = checks.filter(c => c.key !== 'review').every(c => c.done);

        return `
        <h2>Publishing Checklist</h2>
        <p class="step-description">Review your course before publishing</p>
        <div style="background:var(--color-gray-50);border:1px solid var(--color-gray-200);border-radius:var(--radius-lg);padding:16px 18px;margin-bottom:18px;">
            <h3 style="font-size:0.9rem;font-weight:600;color:var(--color-gray-900);margin-bottom:2px;"><i class="fas fa-code-branch"></i> Initial Version</h3>
            <p style="font-size:0.78rem;color:var(--color-gray-500);margin-bottom:12px;">Your course will be published as version <strong>1.0</strong> by default. You can change this if needed.</p>
            <div class="form-row">
                <div class="form-group"><label>Version</label><input type="text" id="courseVersion" class="form-input" value="${this.courseData.version || '1.0'}" style="max-width:120px;"></div>
                <div class="form-group"><label>Version Notes (optional)</label><input type="text" id="versionNotes" class="form-input" value="${this.esc(this.courseData.versionNotes||'')}" placeholder="e.g. Initial release"></div>
            </div>
        </div>
        <div class="checklist">${checks.map(c => `<div class="checklist-item ${c.done?'completed':''}"><span class="checklist-icon"><i class="fas fa-${c.done?'check':'minus'}"></i></span><span class="checklist-text">${c.label}</span></div>`).join('')}</div>
        <div class="publish-actions">
            <button class="nav-btn outline" id="saveDraftPublishBtn"><i class="fas fa-save"></i> Save Draft</button>
            <button class="nav-btn secondary" id="previewPublishBtn"><i class="fas fa-eye"></i> Preview</button>
            <button class="nav-btn primary" id="submitReviewPublishBtn" ${allDone?'':'disabled style="opacity:0.5;cursor:not-allowed;"'}><i class="fas fa-paper-plane"></i> Submit For Review</button>
            <button class="nav-btn primary" id="publishPublishBtn" ${allDone?'':'disabled style="opacity:0.5;cursor:not-allowed;"'} style="background:#059669;"><i class="fas fa-rocket"></i> Publish</button>
        </div>`;
    }

    // ============================================
    // STEP EVENT BINDING
    // ============================================
    bindStepEvents(step) {
        // Since we're using event delegation on #stepContent for drag handles,
        // we only need to bind non-drag events here

        if (step === 1) {
            document.getElementById('shortDesc')?.addEventListener('input', (e) => {
                const countEl = document.getElementById('shortDescCount');
                if (countEl) countEl.textContent = `${e.target.value.length}/300`;
            });
            document.getElementById('addTagBtn')?.addEventListener('click', () => this.addTag());
            document.getElementById('tagInput')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addTag();
            });
            document.querySelectorAll('.tag-chip-remove').forEach(b => b.addEventListener('click', () => {
                this.removeTag(parseInt(b.dataset.index));
            }));
        }

        if (step === 2) {
            document.getElementById('addSectionBtn')?.addEventListener('click', () => this.addSection());
            document.querySelectorAll('.add-lesson-btn').forEach(b => {
                b.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.addLesson(parseInt(b.dataset.section));
                });
            });
            document.querySelectorAll('.section-action-btn.delete').forEach(b => {
                b.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (b.dataset.lesson !== undefined) {
                        this.removeLesson(parseInt(b.dataset.section), parseInt(b.dataset.lesson));
                    } else {
                        this.removeSection(parseInt(b.dataset.section));
                    }
                });
            });
            document.querySelectorAll('.lesson-edit-btn').forEach(b => {
                b.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openLessonModal(parseInt(b.dataset.section), parseInt(b.dataset.lesson));
                });
            });
            document.querySelectorAll('.lesson-title-display').forEach(span => {
                span.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openLessonModal(parseInt(span.dataset.section), parseInt(span.dataset.lesson));
                });
            });
            document.querySelectorAll('.section-title-input').forEach(inp => {
                inp.addEventListener('click', (e) => e.stopPropagation());
            });
            // Drag handles are handled by event delegation on stepContent
        }

        if (step === 3) {
            document.getElementById('addOutcomeBtn')?.addEventListener('click', () => this.addOutcome());
            document.getElementById('newOutcome')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addOutcome();
            });
            document.querySelectorAll('.outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removeOutcome(parseInt(b.dataset.index)));
            });
        }

        if (step === 4) {
            document.getElementById('addPrereqBtn')?.addEventListener('click', () => this.addPrerequisite());
            document.getElementById('newPrereq')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addPrerequisite();
            });
            document.querySelectorAll('#prereqList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removePrerequisite(parseInt(b.dataset.index)));
            });
            // Drag handles are handled by event delegation on stepContent
        }

        if (step === 5) {
            document.getElementById('addAudienceBtn')?.addEventListener('click', () => this.addAudience());
            document.getElementById('newAudience')?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.addAudience();
            });
            document.querySelectorAll('#audienceList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => this.removeAudience(parseInt(b.dataset.index)));
            });
            // Drag handles are handled by event delegation on stepContent
        }

        if (step === 6) {
            document.querySelectorAll('.pricing-option').forEach(b => {
                b.addEventListener('click', () => {
                    document.querySelectorAll('.pricing-option').forEach(x => x.classList.remove('active'));
                    b.classList.add('active');
                    const pricingFields = document.getElementById('pricingFields');
                    if (pricingFields) pricingFields.style.display = b.dataset.type === 'free' ? 'none' : '';
                });
            });
        }

        if (step === 7) {
            document.getElementById('addAttachmentBtn')?.addEventListener('click', () => {
                document.getElementById('attachmentInput')?.click();
            });
            document.getElementById('attachmentInput')?.addEventListener('change', (e) => {
                if (e.target.files) {
                    // Initialize attachment_files array if it doesn't exist
                    if (!this.courseData.attachment_files) {
                        this.courseData.attachment_files = [];
                    }
                    for (let f of e.target.files) {
                        // Store metadata in attachments array for display
                        this.courseData.attachments = [...(this.courseData.attachments||[]), { name: f.name, size: f.size }];
                        // Store actual File object in attachment_files array for FormData
                        this.courseData.attachment_files.push(f);
                    }
                    this.renderStep(7);
                }
            });
            document.querySelectorAll('#attachmentsList .outcome-remove').forEach(b => {
                b.addEventListener('click', () => {
                    const index = parseInt(b.dataset.index);
                    this.courseData.attachments.splice(index, 1);
                    // Also remove from attachment_files if it exists
                    if (this.courseData.attachment_files && this.courseData.attachment_files[index]) {
                        this.courseData.attachment_files.splice(index, 1);
                    }
                    this.renderStep(7);
                });
            });
        }

        if (step === 8) {
            document.getElementById('saveDraftPublishBtn')?.addEventListener('click', () => this.saveDraft(true));
            document.getElementById('previewPublishBtn')?.addEventListener('click', () => this.showToast('Preview would open in new tab'));
            document.getElementById('submitReviewPublishBtn')?.addEventListener('click', () => this.submitForReview());
            document.getElementById('publishPublishBtn')?.addEventListener('click', () => this.publishCourse());
        }
    }

    // ============================================
    // LESSON CONTENT MODAL
    // ============================================
    openLessonModal(si, li) {
        this.collectStepData();
        const lesson = this.courseData.sections[si]?.lessons[li];
        if (!lesson) return;
        this.editingLesson = { sectionIndex: si, lessonIndex: li };
        document.getElementById('modalLessonTitle').textContent = lesson.title || 'Untitled Lesson';
        document.getElementById('modalLessonType').textContent = lesson.type.charAt(0).toUpperCase() + lesson.type.slice(1);

        let html = `
        <div class="form-group"><label>Lesson Title</label><input type="text" id="lessonTitle" class="form-input" value="${this.esc(lesson.title)}"></div>
        <div class="form-row"><div class="form-group"><label>Description</label><input type="text" id="lessonDesc" class="form-input" value="${this.esc(lesson.description||'')}"></div><div class="form-group"><label>Duration (min)</label><input type="number" id="lessonDuration" class="form-input" value="${this.esc(lesson.duration||'')}" min="1"></div></div>
        <div class="form-row"><div class="form-group"><label>Preview Enabled</label><select id="lessonPreview" class="form-select"><option value="1" ${lesson.preview?'selected':''}>Yes</option><option value="0" ${!lesson.preview?'selected':''}>No</option></select></div><div class="form-group"><label>Published</label><select id="lessonPublished" class="form-select"><option value="1" ${lesson.published?'selected':''}>Yes</option><option value="0" ${!lesson.published?'selected':''}>No</option></select></div></div>
        <div class="form-group"><label>Completion Rule</label><select id="lessonCompletionRule" class="form-select"><option value="watch90" ${lesson.completionRule==='watch90'?'selected':''}>Watch ≥90%</option><option value="scroll" ${lesson.completionRule==='scroll'?'selected':''}>Scroll to end</option><option value="manual" ${lesson.completionRule==='manual'?'selected':''}>Manual mark</option><option value="pass" ${lesson.completionRule==='pass'?'selected':''}>Pass quiz</option><option value="submit" ${lesson.completionRule==='submit'?'selected':''}>Submit assignment</option></select></div>`;

        if (lesson.type === 'video') {
            const isFileSource = lesson.content?.videoSource === 'file' || (!lesson.content?.videoSource && !lesson.content?.videoUrl);
            html += `
            <div class="form-group">
                <label>Video Source</label>
                <div class="pricing-toggle" id="videoSourceToggle" style="margin-bottom:0;">
                    <button class="pricing-option ${isFileSource ? 'active' : ''}" data-source="file" type="button">Upload File</button>
                    <button class="pricing-option ${!isFileSource ? 'active' : ''}" data-source="url" type="button">External URL</button>
                </div>
            </div>
            <div id="videoFileSection" style="${!isFileSource ? 'display:none;' : ''}">
                <div class="form-group" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:20px;text-align:center;margin-bottom:16px;">
                    <label style="font-weight:600;display:block;margin-bottom:8px;">Upload Video File</label>
                    <input type="file" id="lessonVideoFile" accept="video/*" class="form-input" style="max-width:300px;margin:0 auto;">
                    ${lesson.content?.videoFileName ? `<p style="margin-top:8px;font-size:0.82rem;color:var(--color-success);"><i class="fas fa-check-circle"></i> Uploaded: ${this.esc(lesson.content.videoFileName)}</p>` : ''}
                    <small style="color:var(--color-gray-400);display:block;margin-top:4px;">Max 2GB · MP4, WebM, MOV</small>
                </div>
            </div>
            <div id="videoUrlSection" style="${isFileSource ? 'display:none;' : ''}">
                <div class="form-group"><label>Video URL</label><input type="url" id="lessonVideoUrl" class="form-input" value="${this.esc(lesson.content?.videoUrl||'')}" placeholder="https://youtube.com/watch?v=... or https://vimeo.com/..."><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Supports YouTube, Vimeo, and direct MP4 links</small></div>
            </div>
            <div class="form-group"><label>Text Content / Description Below Video</label><textarea id="lessonVideoText" class="form-input form-textarea" rows="6" placeholder="Additional text content shown below the video...">${this.esc(lesson.content?.textContent||'')}</textarea></div>
            <div class="form-group"><label>Transcript</label><textarea id="lessonTranscript" class="form-input form-textarea" rows="6" placeholder="Enter video transcript here...&#10;&#10;Format:&#10;00:00 - Welcome to this lesson&#10;00:15 - Today we will cover...">${this.esc(lesson.content?.transcript||'')}</textarea><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Optional. Transcript helps with accessibility and search.</small></div>
            <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--color-gray-200);" id="captionsSection">
                <div class="form-group"><label><i class="fas fa-closed-captioning"></i> Captions / Subtitles</label><p style="font-size:0.78rem;color:var(--color-gray-500);margin-bottom:10px;">Add subtitle files in VTT or SRT format for different languages.</p></div>
                <div id="captionsList">
                    ${(lesson.content?.captions || []).map((cap, i) => `
                        <div class="caption-item-card" data-caption-index="${i}" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--color-gray-200);border-radius:8px;margin-bottom:8px;background:var(--color-gray-50);">
                            <i class="fas fa-closed-captioning" style="color:var(--color-primary-500);font-size:1.1rem;"></i>
                            <div style="flex:1;min-width:0;">
                                <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
                                    <span style="font-weight:600;font-size:0.85rem;color:var(--color-gray-800);">${this.esc(cap.label || cap.language)}</span>
                                    <span style="font-size:0.7rem;padding:2px 8px;background:var(--color-primary-100);color:var(--color-primary-700);border-radius:9999px;">${cap.language.toUpperCase()}</span>
                                    ${cap.isDefault ? '<span style="font-size:0.7rem;padding:2px 8px;background:#D1FAE5;color:#065F46;border-radius:9999px;">Default</span>' : ''}
                                </div>
                                <div style="font-size:0.75rem;color:var(--color-gray-500);">${cap.fileName ? `<i class="fas fa-file-alt"></i> ${this.esc(cap.fileName)} · ${cap.fileFormat?.toUpperCase() || 'VTT'}` : 'No file uploaded'}</div>
                            </div>
                            <div style="display:flex;gap:4px;">
                                ${!cap.isDefault ? `<button class="section-action-btn" onclick="createCoursePage.setDefaultCaption(${i})" title="Set as default" style="color:var(--color-success);"><i class="fas fa-check-circle"></i></button>` : ''}
                                <button class="section-action-btn delete" onclick="createCoursePage.removeCaption(${i})" title="Remove caption"><i class="fas fa-trash-alt"></i></button>
                            </div>
                        </div>
                    `).join('')}
                    ${(lesson.content?.captions || []).length === 0 ? '<p style="color:var(--color-gray-400);font-size:0.82rem;text-align:center;padding:16px;">No captions added yet</p>' : ''}
                </div>
                <div id="addCaptionForm" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:18px;margin-top:10px;">
                    <h4 style="font-size:0.85rem;font-weight:600;color:var(--color-gray-700);margin-bottom:12px;">Add New Caption</h4>
                    <div class="form-row" style="margin-bottom:10px;">
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Language Code *</label><select id="captionLanguage" class="form-input" style="padding:8px 12px;"><option value="en">English (en)</option><option value="es">Spanish (es)</option><option value="fr">French (fr)</option><option value="de">German (de)</option><option value="zh">Chinese (zh)</option><option value="ja">Japanese (ja)</option><option value="ko">Korean (ko)</option><option value="ar">Arabic (ar)</option><option value="pt">Portuguese (pt)</option><option value="ru">Russian (ru)</option><option value="it">Italian (it)</option><option value="other">Other...</option></select></div>
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Label *</label><input type="text" id="captionLabel" class="form-input" placeholder="e.g. English, Spanish" style="padding:8px 12px;"></div>
                    </div>
                    <div class="form-row" style="margin-bottom:10px;">
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Caption File * (.vtt or .srt)</label><input type="file" id="captionFileInput" accept=".vtt,.srt" class="form-input" style="padding:8px 12px;"></div>
                        <div class="form-group" style="margin-bottom:0;"><label style="font-size:0.78rem;">Format</label><select id="captionFormat" class="form-input" style="padding:8px 12px;"><option value="vtt">WebVTT (.vtt)</option><option value="srt">SubRip (.srt)</option></select></div>
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><label style="display:flex;align-items:center;gap:6px;font-size:0.8rem;color:var(--color-gray-600);cursor:pointer;"><input type="checkbox" id="captionIsDefault" style="accent-color:var(--color-primary-600);">Set as default caption</label></div>
                    <button class="add-btn" id="saveCaptionBtn" style="width:100%;"><i class="fas fa-plus"></i> Add Caption</button>
                </div>
            </div>`;
        } else if (lesson.type === 'article') {
            html += `<div class="form-group"><label>Article Content <span class="required">*</span></label><textarea id="lessonArticleText" class="form-input form-textarea" rows="14" placeholder="Write your article content here...">${this.esc(lesson.content?.text||'')}</textarea></div>`;
        } else if (lesson.type === 'pdf') {
            html += `<div class="form-group"><label>PDF URL</label><input type="url" id="lessonPdfUrl" class="form-input" value="${this.esc(lesson.content?.fileUrl||'')}" placeholder="https://example.com/document.pdf"><small style="color:var(--color-gray-400);display:block;margin-top:4px;">Link to an externally hosted PDF file</small></div>
            <div class="form-group" style="border:2px dashed var(--color-gray-300);border-radius:var(--radius-lg);padding:20px;text-align:center;margin-bottom:16px;"><label style="font-weight:600;display:block;margin-bottom:8px;">Or Upload PDF File</label><input type="file" id="lessonPdfFile" accept=".pdf,application/pdf" class="form-input" style="max-width:300px;margin:0 auto;">${lesson.content?.pdfFileName ? `<p style="margin-top:8px;font-size:0.82rem;color:var(--color-success);"><i class="fas fa-check-circle"></i> Uploaded: ${this.esc(lesson.content.pdfFileName)}</p>` : ''}<small style="color:var(--color-gray-400);display:block;margin-top:4px;">Max 50MB · PDF format only</small></div>`;
        } else if (lesson.type === 'quiz') {
            const questions = lesson.content?.questions || [];
            html += `<div class="quiz-questions-container" id="quizQuestionsContainer">${questions.length === 0 ? '<p style="color:var(--color-gray-400);text-align:center;padding:20px;">No questions yet.</p>' : ''}${questions.map((q, qi) => `
                <div class="quiz-question-block" data-question="${qi}"><div class="quiz-question-header"><span class="quiz-question-number">Question ${qi + 1}</span><button class="section-action-btn delete" data-question="${qi}" title="Remove"><i class="fas fa-trash-alt"></i></button></div>
                <div class="form-group"><label>Question Text</label><input type="text" class="form-input quiz-question-text" value="${this.esc(q.text||'')}" placeholder="Enter your question"></div>
                <div class="quiz-options">${(q.options||['','','','']).map((opt, oi) => `<div class="quiz-option-row"><input type="radio" name="correct_q${qi}" class="quiz-correct-radio" ${q.correct===oi?'checked':''}><input type="text" class="form-input quiz-option-text" value="${this.esc(opt)}" placeholder="Option ${oi+1}"></div>`).join('')}</div>
                <div class="form-group" style="margin-top:8px;"><label>Explanation</label><input type="text" class="form-input quiz-explanation" value="${this.esc(q.explanation||'')}" placeholder="Explain the correct answer"></div></div>`).join('')}</div>
            <button class="add-section-btn" id="addQuizQuestionBtn" style="margin-top:12px;"><i class="fas fa-plus"></i> Add Question</button>`;
        } else if (lesson.type === 'assignment') {
            html += `<div class="form-group"><label>Assignment Description</label><textarea id="lessonAssignmentDesc" class="form-input form-textarea" rows="8" placeholder="Describe the assignment...">${this.esc(lesson.content?.description||'')}</textarea></div><div class="form-group"><label>Max Score</label><input type="number" id="lessonAssignmentMaxScore" class="form-input" value="${lesson.content?.maxScore||100}"></div>`;
        } else if (lesson.type === 'external') {
            html += `<div class="form-group"><label>External URL</label><input type="url" id="lessonExternalUrl" class="form-input" value="${this.esc(lesson.content?.url||'')}" placeholder="https://..."></div>`;
        }

        const attachments = lesson.content?.attachments || [];
        html += `
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--color-gray-200);">
            <div class="form-group"><label><i class="fas fa-paperclip"></i> Lesson Attachments</label>
                <div id="lessonAttachmentsList">${attachments.map((a,i)=>`<div class="prereq-item" style="margin-bottom:6px;"><i class="fas fa-paperclip"></i><span>${this.esc(a.name||a)}</span><button class="outcome-remove" data-index="${i}" data-type="lesson-attachment"><i class="fas fa-times"></i></button></div>`).join('')}${attachments.length===0?'<p style="color:var(--color-gray-400);font-size:0.78rem;text-align:center;padding:8px;">No attachments yet</p>':''}</div>
                <button class="add-btn" id="addLessonAttachmentBtn"><i class="fas fa-plus"></i> Add Attachment</button>
                <input type="file" id="lessonAttachmentInput" style="display:none;" multiple>
            </div>
        </div>`;

        document.getElementById('lessonContentArea').innerHTML = html;
        document.getElementById('lessonModalOverlay').style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (lesson.type === 'video') {
            document.querySelectorAll('#videoSourceToggle .pricing-option').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('#videoSourceToggle .pricing-option').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    const source = btn.dataset.source;
                    document.getElementById('videoFileSection').style.display = source === 'file' ? '' : 'none';
                    document.getElementById('videoUrlSection').style.display = source === 'url' ? '' : 'none';
                });
            });
            document.getElementById('saveCaptionBtn')?.addEventListener('click', () => this.saveCaption());
            document.getElementById('captionLanguage')?.addEventListener('change', (e) => {
                const labelMap = { 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'pt': 'Portuguese', 'ru': 'Russian', 'it': 'Italian' };
                const label = document.getElementById('captionLabel');
                if (label && !label.value) label.value = labelMap[e.target.value] || '';
            });
            document.getElementById('captionFileInput')?.addEventListener('change', (e) => {
                const file = e.target.files?.[0];
                if (file) { const ext = file.name.split('.').pop().toLowerCase(); const formatSelect = document.getElementById('captionFormat'); if (formatSelect && (ext === 'vtt' || ext === 'srt')) formatSelect.value = ext; }
            });
        }

        if (lesson.type === 'quiz') {
            document.getElementById('addQuizQuestionBtn')?.addEventListener('click', () => this.addQuizQuestion());
            document.querySelectorAll('.quiz-question-block .section-action-btn.delete').forEach(b => { b.addEventListener('click', () => this.removeQuizQuestion(parseInt(b.dataset.question))); });
        }

        document.getElementById('addLessonAttachmentBtn')?.addEventListener('click', () => document.getElementById('lessonAttachmentInput')?.click());
        document.getElementById('lessonAttachmentInput')?.addEventListener('change', (e) => {
            if (e.target.files && this.editingLesson) {
                const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
                if (lesson) {
                    if (!lesson.content) lesson.content = {};
                    if (!lesson.content.attachments) lesson.content.attachments = [];
                    if (!lesson.content.attachment_files) lesson.content.attachment_files = [];
                    for (let f of e.target.files){
                        // Store metadata for display
                        lesson.content.attachments.push({ name: f.name, size: f.size });
                        // Store actual File object for FormData
                        lesson.content.attachment_files.push(f);
                    }
                    this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
                }
            }
        });
        document.querySelectorAll('#lessonAttachmentsList .outcome-remove').forEach(b => {
            b.addEventListener('click', () => {
                if (this.editingLesson) {
                    const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
                    if (lesson?.content?.attachments) {
                        const index = parseInt(b.dataset.index);
                        lesson.content.attachments.splice(index, 1);
                        // Also remove from attachment_files if it exists
                        if (lesson.content.attachment_files && lesson.content.attachment_files[index]) {
                            lesson.content.attachment_files.splice(index, 1);
                        }
                        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
                    }
                }
            });
        });
    }

    closeLessonModal() {
        document.getElementById('lessonModalOverlay').style.display = 'none';
        document.body.style.overflow = '';
        this.editingLesson = null;
    }

    saveLessonContent() {
        if (!this.editingLesson) return;
        const { sectionIndex, lessonIndex } = this.editingLesson;
        const lesson = this.courseData.sections[sectionIndex]?.lessons[lessonIndex];
        if (!lesson) return;
        const titleEl = document.getElementById('lessonTitle'); if (titleEl) lesson.title = titleEl.value.trim() || lesson.title;
        const descEl = document.getElementById('lessonDesc'); if (descEl) lesson.description = descEl.value.trim();
        const durEl = document.getElementById('lessonDuration'); if (durEl) lesson.duration = durEl.value.trim();
        const prevEl = document.getElementById('lessonPreview'); if (prevEl) lesson.preview = prevEl.value === '1';
        const pubEl = document.getElementById('lessonPublished'); if (pubEl) lesson.published = pubEl.value === '1';
        const ruleEl = document.getElementById('lessonCompletionRule'); if (ruleEl) lesson.completionRule = ruleEl.value;
        const existingAttachments = lesson.content?.attachments || [];
        const existingAttachmentFiles = lesson.content?.attachment_files || [];
        const existingCaptions = lesson.content?.captions || [];
        if (lesson.type === 'video') {
            const activeSource = document.querySelector('#videoSourceToggle .pricing-option.active');
            const videoSource = activeSource?.dataset?.source || 'file';
            const videoFileInput = document.getElementById('lessonVideoFile');
            let videoFile = lesson.content?.videoFile || null; let videoFileName = lesson.content?.videoFileName || '';
            if (videoFileInput?.files[0]) { videoFile = videoFileInput.files[0]; videoFileName = videoFileInput.files[0].name; }
            lesson.content = {
                videoSource,
                videoUrl: document.getElementById('lessonVideoUrl')?.value||'',
                videoFile,
                videoFileName,
                textContent: document.getElementById('lessonVideoText')?.value||'',
                transcript: document.getElementById('lessonTranscript')?.value||'',
                captions: existingCaptions,
                duration: lesson.duration,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        } else if (lesson.type === 'article') {
            lesson.content = {
                text: document.getElementById('lessonArticleText')?.value||'',
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }
        else if (lesson.type === 'pdf') {
            const pdfFileInput = document.getElementById('lessonPdfFile');
            let pdfFile = lesson.content?.pdfFile || null;
            let pdfFileName = lesson.content?.pdfFileName || '';
            if (pdfFileInput?.files[0]) { pdfFile = pdfFileInput.files[0]; pdfFileName = pdfFileInput.files[0].name; }
            lesson.content = {
                fileUrl: document.getElementById('lessonPdfUrl')?.value||'',
                pdfFile,
                pdfFileName,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }
        else if (lesson.type === 'quiz') {
            const questions = [];
            document.querySelectorAll('.quiz-question-block').forEach(block => {
                const text = block.querySelector('.quiz-question-text')?.value||'';
                const options = Array.from(block.querySelectorAll('.quiz-option-text')).map(inp => inp.value);
                const correctRadio = block.querySelector('.quiz-correct-radio:checked');
                const correct = correctRadio ? Array.from(block.querySelectorAll('.quiz-correct-radio')).indexOf(correctRadio) : 0;
                const explanation = block.querySelector('.quiz-explanation')?.value||'';
                if (text) questions.push({ text, options, correct, explanation });
            });
            lesson.content = {
                questions,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }
        else if (lesson.type === 'assignment') {
            lesson.content = {
                description: document.getElementById('lessonAssignmentDesc')?.value||'',
                maxScore: parseInt(document.getElementById('lessonAssignmentMaxScore')?.value)||100,
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }
        else if (lesson.type === 'external') {
            lesson.content = {
                url: document.getElementById('lessonExternalUrl')?.value||'',
                attachments: existingAttachments,
                attachment_files: existingAttachmentFiles
            };
        }
        this.closeLessonModal(); this.renderStep(2); this.showToast('Lesson content saved ✓');
    }

    // ============================================
    // CAPTION MANAGEMENT
    // ============================================
    saveCaption() {
        if (!this.editingLesson) return;
        const language = document.getElementById('captionLanguage')?.value;
        const label = document.getElementById('captionLabel')?.value?.trim();
        const fileInput = document.getElementById('captionFileInput');
        const format = document.getElementById('captionFormat')?.value || 'vtt';
        const isDefault = document.getElementById('captionIsDefault')?.checked || false;
        if (!language) { this.showToast('Please select a language'); return; }
        if (!label) { this.showToast('Please enter a label'); return; }
        if (!fileInput?.files?.[0]) { this.showToast('Please select a caption file'); return; }
        const file = fileInput.files[0];
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'vtt' && ext !== 'srt') { this.showToast('Only .vtt and .srt files are supported'); return; }
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'video') return;
        if (!lesson.content) lesson.content = {};
        if (!lesson.content.captions) lesson.content.captions = [];
        if (isDefault) lesson.content.captions.forEach(cap => cap.isDefault = false);
        const autoDefault = lesson.content.captions.length === 0 ? true : isDefault;
        if (autoDefault) lesson.content.captions.forEach(cap => cap.isDefault = false);
        // Store both metadata and actual File object
        lesson.content.captions.push({
            language,
            label,
            fileName: file.name,
            fileSize: file.size,
            file: file, // Actual File object for FormData
            fileFormat: format,
            isDefault: autoDefault
        });
        this.showToast('Caption added');
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeCaption(index) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.captions) return;
        const wasDefault = lesson.content.captions[index]?.isDefault;
        lesson.content.captions.splice(index, 1);
        if (wasDefault && lesson.content.captions.length > 0) lesson.content.captions[0].isDefault = true;
        this.showToast('Caption removed'); this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    setDefaultCaption(index) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.captions) return;
        lesson.content.captions.forEach((cap, i) => { cap.isDefault = (i === index); });
        this.showToast('Default caption updated'); this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    // ============================================
    // QUIZ MANAGEMENT
    // ============================================
    addQuizQuestion() {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson || lesson.type !== 'quiz') return;
        if (!lesson.content) lesson.content = { questions: [], attachments: [], attachment_files: [] };
        if (!lesson.content.questions) lesson.content.questions = [];
        lesson.content.questions.push({ text: '', options: ['', '', '', ''], correct: 0, explanation: '' });
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    removeQuizQuestion(index) {
        if (!this.editingLesson) return;
        const lesson = this.courseData.sections[this.editingLesson.sectionIndex]?.lessons[this.editingLesson.lessonIndex];
        if (!lesson?.content?.questions) return;
        lesson.content.questions.splice(index, 1);
        this.openLessonModal(this.editingLesson.sectionIndex, this.editingLesson.lessonIndex);
    }

    changeLessonType(si, li, newType) {
        const lesson = this.courseData.sections[si]?.lessons[li];
        if (!lesson) return;
        const oldAtt = lesson.content?.attachments || [];
        const oldAttFiles = lesson.content?.attachment_files || [];
        lesson.type = newType;
        lesson.content = newType === 'quiz' ? { questions: [], attachments: oldAtt, attachment_files: oldAttFiles } : { attachments: oldAtt, attachment_files: oldAttFiles };
        if (newType === 'video') {
            lesson.content.videoSource = 'file';
            lesson.content.videoUrl = '';
            lesson.content.videoFile = null;
            lesson.content.videoFileName = '';
            lesson.content.textContent = '';
            lesson.content.transcript = '';
            lesson.content.captions = [];
        }
        this.renderStep(2);
        this.showToast(`Lesson type changed to ${newType}`);
    }

    // ============================================
    // DRAG AND DROP - COMPLETELY REWRITTEN
    // ============================================

    /**
     * Unified drag start handler
     */
    _startDrag(e, handle, type, data, element) {
        const rect = element.getBoundingClientRect();
        const clientX = e.clientX || e.pageX;
        const clientY = e.clientY || e.pageY;

        this.dragState = {
            active: true,
            type: type,
            sourceSection: data.sourceSection ?? null,
            sourceLesson: data.sourceLesson ?? null,
            sourceIndex: data.sourceIndex ?? null,
            element: element,
            clone: null,
            startX: clientX,
            startY: clientY,
            offsetX: clientX - rect.left,
            offsetY: clientY - rect.top
        };

        // Create visual clone
        const clone = element.cloneNode(true);
        clone.classList.add('drag-clone');
        clone.style.position = 'fixed';
        clone.style.zIndex = '10000';
        clone.style.width = rect.width + 'px';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.pointerEvents = 'none';
        clone.style.opacity = '0.8';
        clone.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
        clone.style.backgroundColor = '#fff';
        document.body.appendChild(clone);

        this.dragState.clone = clone;
        element.classList.add('drag-source');
        document.body.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
    }

    _onMouseMove(e) {
        if (!this.dragState.active) return;

        const ds = this.dragState;
        const clientX = e.clientX;
        const clientY = e.clientY;

        // Move clone
        if (ds.clone) {
            ds.clone.style.left = (clientX - ds.offsetX) + 'px';
            ds.clone.style.top = (clientY - ds.offsetY) + 'px';
        }

        // Check if we've moved enough to show drop targets
        const dx = clientX - ds.startX;
        const dy = clientY - ds.startY;
        if (Math.abs(dx) < 5 && Math.abs(dy) < 5) return;

        // Clear previous hover states
        document.querySelectorAll('.drag-hover, .drag-hover-container').forEach(el => {
            el.classList.remove('drag-hover', 'drag-hover-container');
        });

        // Find element under cursor
        const elUnder = document.elementFromPoint(clientX, clientY);
        if (!elUnder) return;

        if (ds.type === 'section') {
            const sectionBlock = elUnder.closest('.section-block');
            if (sectionBlock && sectionBlock !== ds.element) {
                sectionBlock.classList.add('drag-hover');
            }
        } else if (ds.type === 'lesson') {
            const lessonItem = elUnder.closest('.lesson-item');
            const sectionLessons = elUnder.closest('.section-lessons');

            if (lessonItem && lessonItem !== ds.element) {
                const targetSection = parseInt(lessonItem.dataset.section);
                if (targetSection !== ds.sourceSection && sectionLessons) {
                    sectionLessons.classList.add('drag-hover-container');
                }
                lessonItem.classList.add('drag-hover');
            } else if (sectionLessons) {
                const targetSection = parseInt(sectionLessons.dataset.section);
                if (!isNaN(targetSection) && targetSection !== ds.sourceSection) {
                    sectionLessons.classList.add('drag-hover-container');
                }
            }
        } else if (ds.type === 'prerequisites') {
            const prereqItem = elUnder.closest('.prereq-item');
            if (prereqItem && prereqItem !== ds.element) {
                prereqItem.classList.add('drag-hover');
            }
        } else if (ds.type === 'targetAudience') {
            const audienceItem = elUnder.closest('.audience-item');
            if (audienceItem && audienceItem !== ds.element) {
                audienceItem.classList.add('drag-hover');
            }
        }
    }

    _onMouseUp(e) {
        if (!this.dragState.active) return;

        const ds = this.dragState;

        // Clean up clone
        if (ds.clone) {
            ds.clone.remove();
        }

        // Remove source highlight
        if (ds.element) {
            ds.element.classList.remove('drag-source');
        }

        // Clear all hover states
        document.querySelectorAll('.drag-hover, .drag-hover-container').forEach(el => {
            el.classList.remove('drag-hover', 'drag-hover-container');
        });

        const clientX = e.clientX;
        const clientY = e.clientY;
        const elUnder = document.elementFromPoint(clientX, clientY);

        // Handle drop based on type
        let reordered = false;

        if (ds.type === 'section') {
            const target = elUnder?.closest('.section-block');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.section);
                if (!isNaN(toIndex) && !isNaN(ds.sourceSection)) {
                    this._reorderSections(ds.sourceSection, toIndex);
                    reordered = true;
                }
            }
        } else if (ds.type === 'lesson') {
            const targetLesson = elUnder?.closest('.lesson-item');
            const targetContainer = elUnder?.closest('.section-lessons');

            if (targetLesson && targetLesson !== ds.element) {
                const toSection = parseInt(targetLesson.dataset.section);
                const toLesson = parseInt(targetLesson.dataset.lesson);
                if (!isNaN(toSection) && !isNaN(toLesson) &&
                    !isNaN(ds.sourceSection) && !isNaN(ds.sourceLesson)) {
                    this._reorderLessons(ds.sourceSection, ds.sourceLesson, toSection, toLesson);
                    reordered = true;
                }
            } else if (targetContainer) {
                const toSection = parseInt(targetContainer.dataset.section);
                if (!isNaN(toSection) && toSection !== ds.sourceSection &&
                    !isNaN(ds.sourceSection) && !isNaN(ds.sourceLesson)) {
                    const targetLessons = this.courseData.sections[toSection]?.lessons;
                    this._reorderLessons(ds.sourceSection, ds.sourceLesson, toSection, targetLessons ? targetLessons.length : 0);
                    reordered = true;
                }
            }
        } else if (ds.type === 'prerequisites') {
            const target = elUnder?.closest('.prereq-item');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.index);
                const arr = this.courseData.prerequisites;

                if (!isNaN(ds.sourceIndex) && !isNaN(toIndex) &&
                    ds.sourceIndex >= 0 && ds.sourceIndex < arr.length &&
                    toIndex >= 0 && toIndex < arr.length) {

                    // Perform the reorder
                    const [moved] = arr.splice(ds.sourceIndex, 1);
                    arr.splice(toIndex, 0, moved);
                    reordered = true;
                    this.showToast('Prerequisite reordered successfully ✓');
                }
            }
        } else if (ds.type === 'targetAudience') {
            const target = elUnder?.closest('.audience-item');
            if (target && target !== ds.element) {
                const toIndex = parseInt(target.dataset.index);
                const arr = this.courseData.targetAudience;

                if (!isNaN(ds.sourceIndex) && !isNaN(toIndex) &&
                    ds.sourceIndex >= 0 && ds.sourceIndex < arr.length &&
                    toIndex >= 0 && toIndex < arr.length) {

                    // Perform the reorder
                    const [moved] = arr.splice(ds.sourceIndex, 1);
                    arr.splice(toIndex, 0, moved);
                    reordered = true;
                    this.showToast('Audience reordered successfully ✓');
                }
            }
        }

        // Reset drag state
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        this.dragState = {
            active: false,
            type: null,
            sourceSection: null,
            sourceLesson: null,
            sourceIndex: null,
            element: null,
            clone: null,
            startX: 0,
            startY: 0,
            offsetX: 0,
            offsetY: 0
        };

        // Re-render if something was reordered
        if (reordered) {
            if (ds.type === 'prerequisites') {
                this.renderStep(4);
            } else if (ds.type === 'targetAudience') {
                this.renderStep(5);
            } else {
                this.renderStep(2);
            }
        }
    }

    // Touch event handlers for mobile support
    _onTouchMove(e) {
        if (!this.dragState.active) return;
        e.preventDefault();

        const touch = e.touches[0];
        const fakeEvent = {
            clientX: touch.clientX,
            clientY: touch.clientY,
            startX: this.dragState.startX,
            startY: this.dragState.startY
        };
        this._onMouseMove(fakeEvent);
    }

    _onTouchEnd(e) {
        if (!this.dragState.active) return;

        const touch = e.changedTouches[0];
        const fakeEvent = {
            clientX: touch.clientX,
            clientY: touch.clientY
        };
        this._onMouseUp(fakeEvent);
    }

    _reorderSections(from, to) {
        if (from === to) return;
        const sections = this.courseData.sections;
        if (from < 0 || from >= sections.length || to < 0 || to >= sections.length) return;

        const [moved] = sections.splice(from, 1);
        const adjustedTo = from < to ? to - 1 : to;
        sections.splice(adjustedTo, 0, moved);
        this.showToast('Section moved successfully ✓');
    }

    _reorderLessons(fromS, fromL, toS, toL) {
        if (!this.courseData.sections[fromS] || !this.courseData.sections[toS]) return;

        const src = this.courseData.sections[fromS].lessons;
        const dst = this.courseData.sections[toS].lessons;

        if (!src[fromL]) return;

        const [moved] = src.splice(fromL, 1);

        if (fromS === toS) {
            let adj = toL;
            if (fromL < toL) adj = toL - 1;
            adj = Math.max(0, Math.min(adj, src.length));
            src.splice(adj, 0, moved);
        } else {
            const ins = Math.max(0, Math.min(toL, dst.length));
            dst.splice(ins, 0, moved);
        }

        this.showToast('Lesson moved successfully ✓');
    }

    // ============================================
    // CURRICULUM ACTIONS
    // ============================================
    addSection() {
        this.collectStepData();
        const newId = Math.max(0, ...this.courseData.sections.map(s => s.id)) + 1;
        this.courseData.sections.push({
            id: newId,
            title: 'New Section',
            description: '',
            duration: '',
            lessons: []
        });
        this.renderStep(2);
        this.showToast('Section added');
    }

    removeSection(i) {
        this.collectStepData();
        if (this.courseData.sections.length <= 1) {
            this.showToast('You must have at least one section');
            return;
        }
        this.courseData.sections.splice(i, 1);
        this.renderStep(2);
        this.showToast('Section removed');
    }

    duplicateSection(i) {
        this.collectStepData();
        const orig = this.courseData.sections[i];
        const dup = JSON.parse(JSON.stringify(orig));
        dup.id = Date.now();
        dup.title += ' (Copy)';
        dup.lessons.forEach(l => l.id = Date.now() + Math.random());
        this.courseData.sections.splice(i + 1, 0, dup);
        this.renderStep(2);
        this.showToast('Section duplicated');
    }

    addLesson(si) {
        this.collectStepData();
        this.courseData.sections[si].lessons.push({
            id: Date.now(),
            title: 'New Lesson',
            description: '',
            duration: '',
            type: 'video',
            preview: false,
            published: false,
            completionRule: 'watch90',
            content: {
                videoSource: 'file',
                videoUrl: '',
                videoFile: null,
                videoFileName: '',
                textContent: '',
                transcript: '',
                captions: [],
                duration: '',
                attachments: [],
                attachment_files: []
            }
        });
        this.renderStep(2);
        this.showToast('Lesson added');
    }

    removeLesson(si, li) {
        this.collectStepData();
        this.courseData.sections[si].lessons.splice(li, 1);
        this.renderStep(2);
        this.showToast('Lesson removed');
    }

    duplicateLesson(si, li) {
        this.collectStepData();
        const orig = this.courseData.sections[si].lessons[li];
        const dup = JSON.parse(JSON.stringify(orig));
        dup.id = Date.now();
        dup.title += ' (Copy)';
        // Note: File objects cannot be duplicated via JSON, so attachment_files will be empty in the copy
        // This is intentional as you can't duplicate file references
        dup.content.attachment_files = [];
        this.courseData.sections[si].lessons.splice(li + 1, 0, dup);
        this.renderStep(2);
        this.showToast('Lesson duplicated');
    }

    toggleSectionCollapse(si) {
        const lessonsEl = document.getElementById(`sectionLessons${si}`);
        const iconEl = document.getElementById(`collapseIcon${si}`);
        if (lessonsEl) lessonsEl.classList.toggle('collapsed');
        if (iconEl) iconEl.classList.toggle('rotated');
    }

    // ============================================
    // TAGS, OUTCOMES, PREREQUISITES, AUDIENCE
    // ============================================
    addTag() {
        const i = document.getElementById('tagInput');
        const v = i?.value?.trim();
        if (!v) return;
        if ((this.courseData.tags||[]).includes(v)) {
            this.showToast('Already added');
            return;
        }
        this.courseData.tags = [...(this.courseData.tags||[]), v];
        if (i) i.value = '';
        this.renderStep(1);
    }

    removeTag(i) {
        this.courseData.tags.splice(i, 1);
        this.renderStep(1);
    }

    addOutcome() {
        const i = document.getElementById('newOutcome');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.outcomes.push(v);
        if (i) i.value = '';
        this.renderStep(3);
        this.showToast('Outcome added');
    }

    removeOutcome(i) {
        this.courseData.outcomes.splice(i, 1);
        this.renderStep(3);
        this.showToast('Outcome removed');
    }

    addPrerequisite() {
        const i = document.getElementById('newPrereq');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.prerequisites.push(v);
        if (i) i.value = '';
        this.renderStep(4);
        this.showToast('Prerequisite added');
    }

    removePrerequisite(i) {
        this.courseData.prerequisites.splice(i, 1);
        this.renderStep(4);
        this.showToast('Prerequisite removed');
    }

    addAudience() {
        const i = document.getElementById('newAudience');
        const v = i?.value?.trim();
        if (!v) return;
        this.courseData.targetAudience.push(v);
        if (i) i.value = '';
        this.renderStep(5);
        this.showToast('Audience added');
    }

    removeAudience(i) {
        this.courseData.targetAudience.splice(i, 1);
        this.renderStep(5);
        this.showToast('Audience removed');
    }

    handleThumbnail(file) {
        if (!file) return;
        this.courseData.thumbnail = file;
        this.courseData.thumbnailPreview = URL.createObjectURL(file);
        this.renderStep(7);
        this.showToast('Thumbnail uploaded');
    }

    // ============================================
    // DATA COLLECTION
    // ============================================
    collectStepData() {
        this.courseData.title = document.getElementById('courseTitle')?.value || this.courseData.title || '';
        this.courseData.subtitle = document.getElementById('courseSubtitle')?.value || this.courseData.subtitle || '';
        this.courseData.shortDescription = document.getElementById('shortDesc')?.value || this.courseData.shortDescription || '';
        this.courseData.category = document.getElementById('courseCategory')?.value || this.courseData.category || '';
        this.courseData.subcategory = document.getElementById('courseSubcategory')?.value || this.courseData.subcategory || '';
        this.courseData.level = document.getElementById('courseLevel')?.value || this.courseData.level || 'intermediate';
        this.courseData.language = document.getElementById('courseLanguage')?.value || this.courseData.language || 'en';
        this.courseData.duration = document.getElementById('courseDuration')?.value || this.courseData.duration || '';
        this.courseData.visibility = document.getElementById('courseVisibility')?.value || this.courseData.visibility || 'public';
        this.courseData.fullDescription = document.getElementById('fullDescription')?.value || this.courseData.fullDescription || '';

        document.querySelectorAll('.section-title-input').forEach(i => {
            const si = parseInt(i.dataset.section);
            if (!isNaN(si) && this.courseData.sections[si]) {
                this.courseData.sections[si].title = i.value || this.courseData.sections[si].title || '';
            }
        });

        const priceEl = document.getElementById('coursePrice');
        if (priceEl) {
            const activeOption = document.querySelector('.pricing-option.active');
            this.courseData.priceType = activeOption?.dataset?.type || this.courseData.priceType || 'paid';
            this.courseData.price = parseFloat(priceEl.value) || this.courseData.price || 0;
            this.courseData.discountPrice = document.getElementById('discountPrice')?.value || this.courseData.discountPrice || '';
        }

        const seoTitleEl = document.getElementById('seoTitle');
        if (seoTitleEl) {
            this.courseData.courseTrailer = document.getElementById('courseTrailer')?.value || this.courseData.courseTrailer || '';
            this.courseData.promoVideo = document.getElementById('promoVideo')?.value || this.courseData.promoVideo || '';
            this.courseData.seoTitle = seoTitleEl.value || this.courseData.seoTitle || '';
            this.courseData.seoDescription = document.getElementById('seoDescription')?.value || this.courseData.seoDescription || '';
        }

        this.courseData.version = document.getElementById('courseVersion')?.value?.trim() || this.courseData.version || '1.0';
        this.courseData.versionNotes = document.getElementById('versionNotes')?.value?.trim() || this.courseData.versionNotes || '';
    }

    // ============================================
    // COURSE ACTIONS
    // ============================================
    async publishCourse() {
        this.collectStepData();
        this.courseData.version = document.getElementById('courseVersion')?.value?.trim() || '1.0';
        this.courseData.versionNotes = document.getElementById('versionNotes')?.value?.trim() || '';
        this.courseData.status = 'published';
        this.courseData.reviewStatus = 'approved';
        this.courseData.lastUpdated = new Date();
        this.courseData.versionHistory = [{
            version: this.courseData.version,
            date: new Date(),
            status: 'published',
            notes: this.courseData.versionNotes || 'Initial release'
        }];
        this.showToast(`Course published as v${this.courseData.version}! 🎉`);
    }

    async submitForReview() {
        this.collectStepData();
        this.courseData.status = 'under_review';
        this.courseData.reviewStatus = 'pending';
        const courseData = mapData(this.courseData)
        const newformData = buildFormData(courseData)
        console.log("data that sent to backend:",newformData)
        try{
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/courses/create/",
                {
                    method: 'POST',
                    body: newformData
                }
            );
            const data = await response.json()

            console.log(data)
            this.showToast('Course submitted for review');
        }catch(err){
            console.log(error)
        }

    }

    // ============================================
    // NAVIGATION
    // ============================================
    nextStep() {
        this.collectStepData();
        if (this.currentStep < this.totalSteps) this.goToStep(this.currentStep + 1);
    }

    prevStep() {
        this.collectStepData();
        if (this.currentStep > 1) this.goToStep(this.currentStep - 1);
    }

    goToStep(s) {
        this.collectStepData();
        this.currentStep = s;
        this.renderStep(s);
    }

    updateProgressUI() {
        document.querySelectorAll('.progress-step').forEach(s => {
            const n = parseInt(s.dataset.step);
            s.classList.remove('active', 'completed');
            if (n === this.currentStep) s.classList.add('active');
            else if (n < this.currentStep) s.classList.add('completed');
        });
        document.querySelectorAll('.step-connector').forEach((c, i) => {
            c.classList.toggle('completed', i + 1 < this.currentStep);
        });
        const prevBtn = document.getElementById('prevStepBtn');
        if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'flex' : 'none';
    }

    updateNavigationButtons() {
        const b = document.getElementById('nextStepBtn');
        const stepLabels = ['', '', 'Curriculum', 'Outcomes', 'Prerequisites', 'Target Audience', 'Pricing', 'Media & SEO', 'Publish'];
        if (this.currentStep < this.totalSteps) {
            if (b) {
                b.innerHTML = `Next: ${stepLabels[this.currentStep + 1]} <i class="fas fa-arrow-right"></i>`;
                b.style.display = 'flex';
            }
        } else {
            if (b) b.style.display = 'none';
        }
    }

    startAutoSave() {
        this.autoSaveTimer = setInterval(() => this.saveDraft(false), 30000);
    }

    async saveDraft(show) {
        this.collectStepData();
        // Note: File objects cannot be serialized to JSON, so they won't be saved in localStorage
        // We save a version without file objects
        const draftData = JSON.parse(JSON.stringify(this.courseData, (key, value) => {
            if (value instanceof File || value instanceof Blob||key=="attachments") {
                return undefined; // Skip File/Blob objects
            }
            return value;
        }));
        localStorage.setItem('courseDraft', JSON.stringify(draftData));
        const ind = document.getElementById('autoSaveIndicator');
        if (ind) {
            ind.innerHTML = '<i class="fas fa-save"></i> Saving...';
            ind.className = 'auto-save-indicator saving';
            setTimeout(() => {
                ind.innerHTML = '<i class="fas fa-check-circle"></i> Draft saved';
                ind.className = 'auto-save-indicator';
            }, 600);
        }
        if (show) this.showToast('Draft saved successfully');
    }

    loadDraft() {
        const s = localStorage.getItem('courseDraft');
        if (s) {
            try {
                const d = JSON.parse(s);
                if (d.title || d.sections) {
                    // Merge with defaults, ensuring file arrays exist
                    this.courseData = {
                        ...this.courseData,
                        ...d,
                        // Ensure file arrays are initialized since they can't be saved in JSON
                        attachment_files: [],
                        sections: (d.sections || this.courseData.sections).map(section => ({
                            ...section,
                            lessons: (section.lessons || []).map(lesson => ({
                                ...lesson,
                                content: {
                                    ...lesson.content,
                                    attachment_files: []
                                }
                            }))
                        }))
                    };
                }
            } catch (e) {
                console.warn('Failed to load draft:', e);
            }
        }
    }

    renderAll() {
        this.renderStep(this.currentStep);
    }

    esc(s) {
        if (!s) return '';
        return s.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    hideLoader() {
        const loader = document.getElementById('loadingOverlay');
        if (loader) loader.classList.add('hidden');
    }

    showToast(m) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const t = document.createElement('div');
        t.className = 'toast-popup';
        t.textContent = m;
        container.appendChild(t);
        requestAnimationFrame(() => {
            t.style.opacity = '1';
            t.style.transform = 'translateY(0)';
        });
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateY(20px)';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }
}

// Initialize on DOM ready
let createCoursePage;
document.addEventListener('DOMContentLoaded', () => {
    createCoursePage = new CreateCoursePage();
});
