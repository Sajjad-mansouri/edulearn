// ---------- DOM elements ----------
const form = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const togglePassword = document.getElementById('togglePassword');
const loginButton = document.getElementById('loginButton');
const errorDiv = document.getElementById('errorMessage');

// ---------- Helper functions ----------
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}

function hideError() {
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');
}

function setLoading(isLoading) {
    if (isLoading) {
        loginButton.classList.add('loading');
        loginButton.disabled = true;
    } else {
        loginButton.classList.remove('loading');
        loginButton.disabled = false;
    }
}

// ---------- Get redirect URL from query parameters ----------
function getRedirectUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const redirect = urlParams.get('next');
    const action = urlParams.get('action');

    if (redirect) {
        // Decode the redirect URL
        let redirectUrl = decodeURIComponent(redirect);

        // Add action as a hash or query parameter if needed
        if (action) {
            // You can pass the action to the course page using hash
            // The course page can check for this hash and perform the action
            redirectUrl += `#action=${action}`;
        }

        return redirectUrl;
    }

    // Default redirect URL
    return window.location.origin + '/account/profile';
}

// ---------- Check if user is already logged in ----------
async function checkExistingAuth() {
    const auth = new Auth({
        baseURL: window.location.origin + '/api/v1/account/auth',
        loginPath: '/login/',
    });

    try {
        const response = await auth.authenticatedRequest(
            window.location.origin + '/api/v1/account/auth/current_user/',
            { method: 'GET' }
        );

        if (response.ok) {
            // User is already logged in, redirect to destination
            window.location.href = getRedirectUrl();
        }
    } catch (error) {
        // User is not logged in, stay on login page
        console.log('User not authenticated, showing login form');
    }
}

// ---------- Toggle password visibility ----------
togglePassword.addEventListener('click', () => {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    togglePassword.textContent = type === 'password' ? 'Show' : 'Hide';
});

// ---------- Form submission ----------
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        showError('Please fill in both fields.');
        return;
    }

    setLoading(true);

    const auth = new Auth({
        baseURL: window.location.origin + '/api/v1/account/auth',
        loginPath: '/login/',
    });

    try {
        const result = await auth.login(username, password);

        if (result.success) {
            // Get the redirect URL and navigate to it
            const redirectUrl = getRedirectUrl();
            window.location.href = redirectUrl;
        } else {
            showError(result.error || 'Invalid username or password.');
        }
    } catch (err) {
        showError('A network error occurred. Please try again.');
        console.error(err);
    } finally {
        setLoading(false);
    }
});

// ---------- Initial check ----------
// Check if user is already logged in when page loads
document.addEventListener('DOMContentLoaded', () => {
    checkExistingAuth();
});
