/**
 * Common authentication utilities
 * Shared functions for login and register pages
 */

// ===== PASSWORD HASHING =====

// Pure-JS SHA-256 — works over HTTP and in all browsers (no secure context needed).
// Based on the FIPS 180-4 specification.
function _sha256(msgBuffer) {
    const K = [
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ];
    let h = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];

    const bytes = new Uint8Array(msgBuffer);
    const bitLen = bytes.length * 8;
    const padLen = ((bytes.length + 8) & ~63) + 64;
    const padded = new Uint8Array(padLen);
    padded.set(bytes);
    padded[bytes.length] = 0x80;
    new DataView(padded.buffer).setUint32(padLen - 4, bitLen, false);

    const r = (x, n) => (x >>> n) | (x << (32 - n));
    for (let i = 0; i < padLen; i += 64) {
        const w = new Array(64);
        const dv = new DataView(padded.buffer, i, 64);
        for (let j = 0; j < 16; j++) w[j] = dv.getUint32(j * 4, false);
        for (let j = 16; j < 64; j++) {
            const s0 = r(w[j-15],7) ^ r(w[j-15],18) ^ (w[j-15]>>>3);
            const s1 = r(w[j-2],17) ^ r(w[j-2],19) ^ (w[j-2]>>>10);
            w[j] = (w[j-16] + s0 + w[j-7] + s1) >>> 0;
        }
        let [a,b,c,d,e,f,g,hh] = h;
        for (let j = 0; j < 64; j++) {
            const S1 = r(e,6) ^ r(e,11) ^ r(e,25);
            const ch = (e & f) ^ (~e & g);
            const t1 = (hh + S1 + ch + K[j] + w[j]) >>> 0;
            const S0 = r(a,2) ^ r(a,13) ^ r(a,22);
            const maj = (a & b) ^ (a & c) ^ (b & c);
            const t2 = (S0 + maj) >>> 0;
            hh=g; g=f; f=e; e=(d+t1)>>>0; d=c; c=b; b=a; a=(t1+t2)>>>0;
        }
        h = h.map((v,i) => (v + [a,b,c,d,e,f,g,hh][i]) >>> 0);
    }
    const out = new Uint8Array(32);
    h.forEach((v,i) => new DataView(out.buffer).setUint32(i*4, v, false));
    return out.buffer;
}

async function hashPassword(password) {
    const encoder = new TextEncoder();
    let hash = encoder.encode(password).buffer;
    for (let i = 0; i < 1000; i++) {
        hash = _sha256(hash);
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
