// ==================== NAVBAR UTILITY FUNCTIONS ====================

const auth = new Auth({
    "baseURL": window.location.origin + '/api/v1/account/auth',
    "onLogout": ()=>{}
});

const baseUrl = window.location.origin;

class NavbarManager {
    constructor() {
        this.userAuth = null;
        this.userMenuActive = false;
        this.init();
    }

    async init() {
        await this.checkAuth();
        this.updateUIForAuth();
        this.bindGlobalClickHandler();
    }

    escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    }

    async checkAuth() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/auth/current_user/",
                {
                    method: "GET",
                }
            );

            if (!response.ok) throw new Error('Failed to fetch current user');
            const data = await response.json();
            console.log(data)
            this.userAuth = data;
            console.log("Navbar user auth data:", this.userAuth); // Debug log

        } catch (error) {
            console.error('Error loading current user:', error);
            this.userAuth = { is_authenticated: false };
        }
    }

    async logout() {
        try {
            const response = await auth.authenticatedRequest(
                baseUrl + "/api/v1/account/auth/logout/",
                {
                    method: "POST",
                }
            );

            if (response.ok) {
                // Clear any stored auth tokens
                if (typeof auth.clearTokens === 'function') {
                    auth.clearTokens();
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Logout error:', error);
            return false;
        }
    }

    bindGlobalClickHandler() {
        document.addEventListener('click', (e) => {
            // Close user menu when clicking outside
            if (this.userMenuActive && !e.target.closest('.user-menu-container') && !e.target.closest('.user-avatar-btn')) {
                this.closeUserMenu();
            }
        });
    }

    closeUserMenu() {
        const userDropdown = document.getElementById('userDropdownMenu');
        if (userDropdown) {
            userDropdown.style.display = 'none';
        }
        this.userMenuActive = false;
    }

    toggleUserMenu() {
        const userDropdown = document.getElementById('userDropdownMenu');
        if (userDropdown) {
            const isVisible = userDropdown.style.display === 'block';
            userDropdown.style.display = isVisible ? 'none' : 'block';
            this.userMenuActive = !isVisible;
        }
    }

    updateUIForAuth() {
        const topNavRight = document.querySelector('.top-nav-right');
        if (!topNavRight) {
            console.error('Top nav right element not found');
            return;
        }

        // Check if user is authenticated
        if (this.userAuth && this.userAuth.is_authenticated) {
            // Check if user is instructor to hide "Teach on EduLearn" link

            let teachLink  = ""
            if (!this.userAuth.is_instructor) {
                teachLink = `
                                    <a href="/account/auth/register/instructor/" class="nav-link teach-link">
                    <i class="fas fa-chalkboard-user"></i> Teach on EduLearn
                </a>
                `

            }

            // Get user avatar or create a fallback
            const avatarUrl = this.userAuth.avatar ;

            const userName = this.userAuth.username;

            topNavRight.innerHTML = `
                ${teachLink}
                <div class="user-menu-container" style="position: relative; display: inline-block;">
                    <button class="user-avatar-btn" id="userAvatarBtn"
                            style="background: none; border: none; cursor: pointer; padding: 0; display: flex; align-items: center; gap: 8px;">
                        <img src="${this.escapeHtml(avatarUrl)}"
                             alt="${this.escapeHtml(userName)}"
                             style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #8B5CF6; object-fit: cover;">

                    </button>
                    <div id="userDropdownMenu"
                         style="display: none; position: absolute; right: 0; top: calc(100% + 8px); background: white;
                                border: 1px solid #E5E7EB; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                                min-width: 200px; z-index: 10000; padding: 8px 0;">
                        <a href="/dashboard"
                           style="display: flex; align-items: center; gap: 12px; padding: 10px 16px; color: #374151;
                                  text-decoration: none; transition: background 0.2s;"
                           onmouseover="this.style.background='#F3F4F6'"
                           onmouseout="this.style.background='none'">
                            <i class="fas fa-tachometer-alt" style="color: #8B5CF6; width: 20px;"></i>
                            Dashboard
                        </a>
                        <a href="/profile"
                           style="display: flex; align-items: center; gap: 12px; padding: 10px 16px; color: #374151;
                                  text-decoration: none; transition: background 0.2s;"
                           onmouseover="this.style.background='#F3F4F6'"
                           onmouseout="this.style.background='none'">
                            <i class="fas fa-user" style="color: #8B5CF6; width: 20px;"></i>
                            Profile
                        </a>
                        <div style="border-top: 1px solid #E5E7EB; margin: 8px 0;"></div>
                        <button onclick="navbarManager.handleLogout()"
                                style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 10px 16px;
                                       color: #EF4444; background: none; border: none; cursor: pointer;
                                       transition: background 0.2s;"
                                onmouseover="this.style.background='#FEF2F2'"
                                onmouseout="this.style.background='none'">
                            <i class="fas fa-sign-out-alt" style="width: 20px;"></i>
                            Logout
                        </button>
                    </div>
                </div>

            `;

            // Bind user menu events
            const avatarBtn = document.getElementById('userAvatarBtn');
            if (avatarBtn) {
                avatarBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleUserMenu();
                });
            }
        } else {
            // Not authenticated - show login/signup buttons
            topNavRight.innerHTML = `
                <a href="/account/auth/register/instructor/" class="nav-link teach-link">
                    <i class="fas fa-chalkboard-user"></i> Teach on EduLearn
                </a>
                <a href="/account/auth/login/" class="btn-login">Log In</a>
                <a href="/account/auth/register/student/" class="btn-signup">Sign Up</a>
            `;
        }
    }

    async handleLogout() {
        const success = await this.logout();
        if (success) {
            this.showToast('Logged out successfully');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            this.showToast('Failed to logout', 'error');
        }
    }

    showToast(message, type = 'success') {
        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#3B82F6'
        };

        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: #1F2937; color: #FFF; padding: 12px 24px; border-radius: 8px;
            font-size: 0.875rem; z-index: 9999; box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            display: flex; align-items: center; gap: 8px;
            border-left: 4px solid ${colors[type] || colors.success};
        `;

        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        toast.innerHTML = `
            <i class="fas fa-${icons[type] || icons.success}" style="color: ${colors[type] || colors.success};"></i>
            ${message}
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }
}

// Initialize navbar
let navbarManager;
document.addEventListener('DOMContentLoaded', () => {
    navbarManager = new NavbarManager();
    window.navbarManager = navbarManager;
});
