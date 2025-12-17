/**
 * Common authentication utilities
 * Shared functions for login and register pages
 */

// ===== PASSWORD HASHING =====
/**
 * Hash password client-side using SHA-256 x1000 iterations
 * @param {string} password - Plain text password
 * @returns {Promise<string>} Hex-encoded hash
 */
async function hashPassword(password) {
    const encoder = new TextEncoder();
    let hash = encoder.encode(password);

    for (let i = 0; i < 1000; i++) {
        hash = await crypto.subtle.digest('SHA-256', hash);
    }

    return Array.from(new Uint8Array(hash))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// ===== FORM VALIDATION HELPERS =====
/**
 * Validate email format
 * @param {string} email - Email address to validate
 * @returns {boolean} True if valid email format
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Display error message for a form field
 * @param {string} fieldId - ID of the form field
 * @param {string} message - Error message to display
 */
function showError(fieldId, message) {
    const errorElement = document.getElementById(`${fieldId}-error`);
    const inputElement = document.getElementById(fieldId);

    if (errorElement && inputElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        inputElement.classList.add('error');
    }
}

/**
 * Clear error message for a form field
 * @param {string} fieldId - ID of the form field
 */
function clearError(fieldId) {
    const errorElement = document.getElementById(`${fieldId}-error`);
    const inputElement = document.getElementById(fieldId);

    if (errorElement && inputElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
        inputElement.classList.remove('error');
    }
}

/**
 * Clear all error messages for specified fields
 * @param {string[]} fieldIds - Array of field IDs to clear
 */
function clearAllErrors(fieldIds) {
    fieldIds.forEach(clearError);
}

// ===== UI FEEDBACK =====
/**
 * Show alert message
 * @param {string} message - Alert message text
 * @param {string} type - Alert type ('success' or 'error')
 */
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    if (alert) {
        alert.textContent = message;
        alert.className = `alert alert-${type}`;
        alert.style.display = 'block';
    }
}

/**
 * Hide alert message
 */
function hideAlert() {
    const alert = document.getElementById('alert');
    if (alert) {
        alert.style.display = 'none';
    }
}

/**
 * Set loading state for submit button
 * @param {boolean} loading - True to show loading, false to hide
 */
function setLoading(loading) {
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');

    if (btnText && btnLoader && submitBtn) {
        if (loading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
            submitBtn.disabled = true;
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            submitBtn.disabled = false;
        }
    }
}
