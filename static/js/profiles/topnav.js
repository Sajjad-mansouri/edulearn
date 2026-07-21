// ============================================
// TOP NAVIGATION CONTROLLER
// ============================================
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
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => { e.stopPropagation(); document.getElementById('userDropdown')?.classList.toggle('open'); });
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
            const response = await auth.authenticatedRequest(window.location.origin + "/api/v1/account/current-user/");
            this.userData = await response.json()
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
        //     role: 'student'
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
        this.loadUserData();
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
