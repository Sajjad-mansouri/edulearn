    // DOM elements
    const registerCard = document.getElementById('registerCard');
    const successCard = document.getElementById('successCard');
    const registerForm = document.getElementById('registerForm');
    const errorDiv = document.getElementById('errorMessage');
    const registerButton = document.getElementById('registerButton');

    // Helper functions
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
        registerButton.classList.add('loading');
        registerButton.disabled = true;
      } else {
        registerButton.classList.remove('loading');
        registerButton.disabled = false;
      }
    }

    // Password toggle for both fields
    document.querySelectorAll('.password-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const input = document.getElementById(targetId);
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        btn.textContent = type === 'password' ? 'Show' : 'Hide';
      });
    });

    // Registration function using Auth's base URL
    async function registerUser(userData) {
      const auth = new Auth({
        baseURL: window.location.origin + '/api/v1/account/auth/',
      });

      const url = `${auth.baseURL}/register/`;
      console.log(userData)
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(userData),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          // Extract error details from DRF-style responses
          let errorMsg = '';
          if (typeof errorData === 'string') {
            errorMsg = errorData;
          } else if (errorData.detail) {
            errorMsg = errorData.detail;
          } else {
            // Combine field errors
            const messages = [];
            for (const [key, value] of Object.entries(errorData)) {
              if (Array.isArray(value)) {
                messages.push(...value);
              } else {
                messages.push(value);
              }
            }
            errorMsg = messages.join(' ') || 'Registration failed.';
          }
          return { success: false, error: errorMsg };
        }

        return { success: true };
      } catch (err) {
        return { success: false, error: 'Network error. Please try again.' };
      }
    }

    // Form submission
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();

      const firstName = document.getElementById('firstName').value.trim();
      const lastName = document.getElementById('lastName').value.trim();
      const email = document.getElementById('email').value.trim();
      const username = document.getElementById('username').value.trim();
      const password1 = document.getElementById('password1').value;
      const password2 = document.getElementById('password2').value;

      // Basic validation
      if (!firstName || !lastName || !email || !username || !password1 || !password2) {
        showError('All fields are required.');
        return;
      }

      if (password1 !== password2) {
        showError('Passwords do not match.');
        return;
      }

      const userData = {
        first_name: firstName,
        last_name: lastName,
        email,
        username,
        password1: password1,
        password2: password2,
      };

      setLoading(true);

      const result = await registerUser(userData);

      if (result.success) {
        // Show success card, hide registration card
        registerCard.classList.add('hidden');
        successCard.classList.remove('hidden');
      } else {
        showError(result.error);
      }

      setLoading(false);
    });
