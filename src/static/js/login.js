/**
 * Login page functionality
 * Handles user authentication and form validation
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('loginForm');
    const password = document.getElementById('password');
    const identifier = document.getElementById('identifier');

    // Auto-focus on the first field
    identifier.focus();

    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset errors and alerts
        clearAllErrors(['identifier', 'password']);
        hideAlert();

        // Validation
        let isValid = true;

        if (identifier.value.length < 3) {
            showError('identifier', 'Veuillez entrer votre nom d\'utilisateur ou email');
            isValid = false;
        }

        if (password.value.length < 1) {
            showError('password', 'Veuillez entrer votre mot de passe');
            isValid = false;
        }

        if (!isValid) return;

        // Submit form
        setLoading(true);

        try {
            // Hash password client-side (SHA-256 x1000)
            const hashedPassword = await hashPassword(password.value);

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    identifier: identifier.value,
                    password: hashedPassword,
                    remember: document.getElementById('remember').checked
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Store tokens (Note: tokens are also in httponly cookies)
                if (data.access_token) {
                    localStorage.setItem('access_token', data.access_token);
                }
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }

                showAlert('Connexion réussie ! Redirection...', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                showAlert(data.message || 'Identifiants incorrects', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('Erreur de connexion au serveur', 'error');
        } finally {
            setLoading(false);
        }
    });
});
