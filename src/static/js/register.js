/**
 * Register page functionality
 * Handles user registration, password strength checking, and form validation
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('registerForm');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');
    const username = document.getElementById('username');
    const email = document.getElementById('email');

    // ===== PASSWORD STRENGTH CHECKER =====
    /**
     * Check password strength
     * @param {string} password - Password to check
     * @returns {number} Strength score (0-4)
     */
    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;
        return Math.min(strength, 4);
    }

    /**
     * Update password strength visual indicator
     * @param {number} strength - Strength score (0-4)
     */
    function updatePasswordStrength(strength) {
        const strengthBar = document.querySelector('.strength-bar');
        const colors = ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#10b981'];
        const widths = ['20%', '40%', '60%', '80%', '100%'];

        if (password.value.length === 0) {
            strengthBar.style.width = '0%';
            return;
        }

        strengthBar.style.width = widths[strength];
        strengthBar.style.backgroundColor = colors[strength];
    }

    // ===== EVENT LISTENERS =====
    // Password strength indicator
    password.addEventListener('input', function() {
        const strength = checkPasswordStrength(this.value);
        updatePasswordStrength(strength);
    });

    // Password confirmation validation
    confirmPassword.addEventListener('input', function() {
        if (this.value !== password.value) {
            showError('confirm-password', 'Les mots de passe ne correspondent pas');
        } else {
            clearError('confirm-password');
        }
    });

    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset errors and alerts
        clearAllErrors(['username', 'email', 'password', 'confirm-password']);
        hideAlert();

        // Validation
        let isValid = true;

        if (username.value.length < 3) {
            showError('username', 'Le nom d\'utilisateur doit contenir au moins 3 caractères');
            isValid = false;
        }

        if (!isValidEmail(email.value)) {
            showError('email', 'Adresse email invalide');
            isValid = false;
        }

        if (password.value.length < 8) {
            showError('password', 'Le mot de passe doit contenir au moins 8 caractères');
            isValid = false;
        }

        if (password.value !== confirmPassword.value) {
            showError('confirm-password', 'Les mots de passe ne correspondent pas');
            isValid = false;
        }

        if (!isValid) return;

        // Submit form
        setLoading(true);

        try {
            // Hash password client-side (SHA-256 x1000)
            const hashedPassword = await hashPassword(password.value);

            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username.value,
                    email: email.value,
                    password: hashedPassword
                })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(data.message || 'Compte créé avec succès ! Redirection...', 'success');
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 1500);
            } else {
                showAlert(data.message || 'Erreur lors de la création du compte', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            showAlert('Erreur de connexion au serveur', 'error');
        } finally {
            setLoading(false);
        }
    });
});
