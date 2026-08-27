// ============================================
// TOP NAVIGATION CONTROLLER
// ============================================
const baseUrl = window.location.origin;
const auth = new Auth({
    "baseURL": window.location.origin + '/api/v1/account/auth',
    "onLogout": ()=>{window.location.href = baseUrl + '/account/auth/login'}
})

class TopNavController {
    constructor() {
        this.userData = null;
        this.notificationCount = 0;
        this.messageCount = 0;
        this.init();
    }

    async init() {
        this.bindDropdownEvents();
        await this.loadUserData();
        await this.loadNotificationCount();
        await this.loadMessageCount();
        this.updateNavUI();
        this.updateSwitchButton();
        this.updateDropdownMenu();

        // Poll for new notifications every 60 seconds
        setInterval(() => this.loadNotificationCount(), 60000);
        setInterval(() => this.loadMessageCount(), 60000);
    }

    // ============================================
    // DROPDOWN EVENTS
    // ============================================
    bindDropdownEvents() {
        const userMenuBtn = document.getElementById('userMenuBtn');
        const userDropdown = document.getElementById('userDropdown');
        const hamburgerBtn = document.getElementById('hamburgerBtn');
        const sidebar = document.getElementById('appSidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');

        document.getElementById('hamburgerBtn')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.toggle('open'));
        document.getElementById('mobileMenuBtn')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('appSidebar')?.classList.toggle('open'); });
        document.getElementById('sidebarOverlay')?.addEventListener('click', () => document.getElementById('appSidebar')?.classList.remove('open'));
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => { console.log("clicked"); e.stopPropagation(); console.log(document.getElementById('userDropdown')); document.getElementById('userDropdown')?.classList.toggle('open'); });
        document.addEventListener('click', (e) => { if (!e.target.closest('.user-menu-wrapper')) document.getElementById('userDropdown')?.classList.remove('open'); });

        // Highlight current page in dropdown
        this.highlightCurrentPage();
    }

    // ============================================
    // DATA LOADING
    // ============================================
    async loadUserData() {
        // ==========================================
        // REAL API CALL
        // ==========================================
        try {
            const response = await auth.authenticatedRequest(window.location.origin + "/api/v1/account/auth/current-user/");
            if (!response.ok) {
                this.userData = null;
                return;
            }
            this.userData = await response.json();
        } catch (error) {
            console.error('Failed to load user data:', error);
        }

        // ==========================================
        // DUMMY DATA
        // ==========================================
        // this.userData = {
        //     id: 1,
        //     first_name: 'John',
        //     last_name: 'Doe',
        //     email: 'john.doe@email.com',
        //     avatar_url: null, // Will use UI Avatars fallback
        //     role: 'student',
        //     is_instructor: true,
        //     is_student: true
        // };
    }

    async loadNotificationCount() {
        // ==========================================
        // REAL API CALL
        // ==========================================
        // try {
        //     const data = await ApiService.get('/notifications/unread-count/');
        //     this.notificationCount = data.count || 0;
        // } catch (error) {
        //     console.error('Failed to load notifications:', error);
        // }

        // ==========================================
        // DUMMY DATA
        // ==========================================
        this.notificationCount = 3;
        this.updateNotificationBadge();
    }

    async loadMessageCount() {
        // ==========================================
        // REAL API CALL
        // ==========================================
        // try {
        //     const data = await ApiService.get('/messages/unread-count/');
        //     this.messageCount = data.count || 0;
        // } catch (error) {
        //     console.error('Failed to load messages:', error);
        // }

        // ==========================================
        // DUMMY DATA
        // ==========================================
        this.messageCount = 2;
        this.updateMessageBadge();
    }

    // ============================================
    // UI UPDATES
    // ============================================
    updateNavUI() {
        this.updateAvatar();
        this.updateUserInfo();
        this.updateNotificationBadge();
        this.updateMessageBadge();
        this.updateSwitchButton();
        this.updateDropdownMenu();
    }

    updateAvatar() {
        if (!this.userData) return;

        const avatarImg = document.querySelector('.user-avatar-img');
        const dropdownAvatar = document.querySelector('.dropdown-user-avatar');

        const avatarUrl = this.userData.avatar_url ||
            `https://ui-avatars.com/api/?name=${encodeURIComponent(this.userData.first_name || '')}+${encodeURIComponent(this.userData.last_name || '')}&background=4F46E5&color=fff&size=64`;

        if (avatarImg) {
            avatarImg.src = avatarUrl;
            avatarImg.alt = `${this.userData.first_name || ''} ${this.userData.last_name || ''}`;
        }

        if (dropdownAvatar) {
            dropdownAvatar.src = this.userData.avatar_url ||
                `https://ui-avatars.com/api/?name=${encodeURIComponent(this.userData.first_name || '')}+${encodeURIComponent(this.userData.last_name || '')}&background=4F46E5&color=fff&size=88`;
        }
    }

    updateUserInfo() {
        if (!this.userData) return;

        const nameEl = document.querySelector('.dropdown-user-name');
        const emailEl = document.querySelector('.dropdown-user-email');

        if (nameEl) {
            nameEl.textContent = `${this.userData.first_name || ''} ${this.userData.last_name || ''}`;
        }

        if (emailEl) {
            emailEl.textContent = this.userData.email || '';
        }
    }

    updateSwitchButton() {
        const switchBtn = document.getElementById('switchRoleBtn');

        if (switchBtn) {
            if (this.userData && this.userData.is_instructor && this.userData.is_student) {
                // Show switch button only if user is both student and instructor
                switchBtn.style.display = 'flex';
            } else {
                switchBtn.style.display = 'none';
            }
        }
    }

    updateNotificationBadge() {
        const badge = document.querySelector('.icon-button .fa-bell')?.parentElement?.querySelector('.icon-badge');
        // More reliable selector
        const notifBtn = document.querySelector('.icon-button .fa-bell')?.closest('.icon-button');
        const notifBadge = notifBtn?.querySelector('.icon-badge');

        if (notifBadge) {
            if (this.notificationCount > 0) {
                notifBadge.textContent = this.notificationCount > 99 ? '99+' : this.notificationCount;
                notifBadge.style.display = 'flex';
            } else {
                notifBadge.textContent = '0';
                notifBadge.style.display = 'none';
            }
        }
    }

    updateMessageBadge() {
        const msgBtn = document.querySelector('.icon-button .fa-envelope')?.closest('.icon-button');
        const msgBadge = msgBtn?.querySelector('.icon-badge');

        if (msgBadge) {
            if (this.messageCount > 0) {
                msgBadge.textContent = this.messageCount > 99 ? '99+' : this.messageCount;
                msgBadge.style.display = 'flex';
            } else {
                msgBadge.textContent = '0';
                msgBadge.style.display = 'none';
            }
        }
    }

    // ============================================
    // DROPDOWN MENU UPDATE BASED ON USER ROLE
    // ============================================
    updateDropdownMenu() {
        const dropdown = document.getElementById('userDropdown');
        if (!dropdown || !this.userData) return;
        console.log(this.userData)
        const isStudent = this.userData.is_student || this.userData.role === 'student';
        const isInstructor = this.userData.is_instructor || this.userData.role === 'instructor';

        let menuHTML = '';

        // User info card
        menuHTML += `
            <div class="dropdown-user-card">
                <img src="${this.userData.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(this.userData.first_name || '')}+${encodeURIComponent(this.userData.last_name || '')}&background=4F46E5&color=fff&size=88`}"
                     alt="Avatar" class="dropdown-user-avatar">
                <div>
                    <span class="dropdown-user-name">${this.userData.first_name || ''} ${this.userData.last_name || ''}</span>
                    <span class="dropdown-user-email">${this.userData.email || ''}</span>
                </div>
            </div>
            <div class="dropdown-separator"></div>
        `;

        // If user is both student and instructor
        if (isStudent && isInstructor) {
            menuHTML += `
                <a href="/student/profile" class="dropdown-item" data-role="student-profile">
                    <i class="fas fa-user-graduate"></i> Student Profile
                </a>
                <a href="/student/dashboard" class="dropdown-item" data-role="student-dashboard">
                    <i class="fas fa-th-large"></i> Student Dashboard
                </a>
                <div class="dropdown-separator"></div>
                <a href="/instructor/profile" class="dropdown-item" data-role="instructor-profile">
                    <i class="fas fa-chalkboard-user"></i> Instructor Profile
                </a>
                <a href="/instructor/dashboard" class="dropdown-item" data-role="instructor-dashboard">
                    <i class="fas fa-chalkboard"></i> Instructor Dashboard
                </a>
            `;
        }
        // If user is only student
        else if (isStudent) {
            menuHTML += `
                <a href="/student/profile" class="dropdown-item active" data-role="student-profile">
                    <i class="fas fa-user"></i> View Profile
                </a>
                <a href="/student/dashboard" class="dropdown-item" data-role="student-dashboard">
                    <i class="fas fa-th-large"></i> Dashboard
                </a>
            `;
        }
        // If user is only instructor
        else if (isInstructor) {
            menuHTML += `
                <a href="/instructor/profile" class="dropdown-item active" data-role="instructor-profile">
                    <i class="fas fa-user"></i> View Profile
                </a>
                <a href="/instructor/dashboard" class="dropdown-item" data-role="instructor-dashboard">
                    <i class="fas fa-th-large"></i> Dashboard
                </a>
            `;
        }

        // Settings and Help
        menuHTML += `
            <div class="dropdown-separator"></div>
            <a href="/account/settings" class="dropdown-item">
                <i class="fas fa-cog"></i> Settings
            </a>
            <a href="/help" class="dropdown-item">
                <i class="fas fa-circle-question"></i> Help
            </a>
            <div class="dropdown-separator"></div>
            <a href="/logout" class="dropdown-item logout-item">
                <i class="fas fa-right-from-bracket"></i> Logout
            </a>
        `;

        dropdown.innerHTML = menuHTML;

        // Re-highlight current page
        this.highlightCurrentPage();
    }

    // ============================================
    // SWITCH ROLE
    // ============================================
    switchToInstructor() {
        if (this.userData && this.userData.is_instructor) {
            window.location.href = '/instructor/dashboard';
        }
    }

    switchToStudent() {
        if (this.userData && this.userData.is_student) {
            window.location.href = '/student/dashboard';
        }
    }

    // ============================================
    // HELPER: HIGHLIGHT CURRENT PAGE IN DROPDOWN
    // ============================================
    highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const dropdownItems = document.querySelectorAll('.dropdown-item');

        dropdownItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                dropdownItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            }
        });
    }

    // ============================================
    // PUBLIC METHODS (can be called from other scripts)
    // ============================================
    refreshAll() {
        this.loadUserData().then(() => {
            this.updateNavUI();
            this.updateDropdownMenu();
        });
        this.loadNotificationCount();
        this.loadMessageCount();
    }

    setNotificationCount(count) {
        this.notificationCount = count;
        this.updateNotificationBadge();
    }

    setMessageCount(count) {
        this.messageCount = count;
        this.updateMessageBadge();
    }

    incrementNotifications() {
        this.notificationCount++;
        this.updateNotificationBadge();
    }

    incrementMessages() {
        this.messageCount++;
        this.updateMessageBadge();
    }
}

// ============================================
// BOOTSTRAP
// ============================================
let topNav;
document.addEventListener('DOMContentLoaded', () => {
    topNav = new TopNavController();
});
