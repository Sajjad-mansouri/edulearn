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
        baseURL: window.location.origin + '/api/v1/accounts',
        loginPath: '/login/',
      });

      try {
        const result = await auth.login(username, password);

        if (result.success) {
          window.location.href = '/';   // Change to your dashboard URL
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
