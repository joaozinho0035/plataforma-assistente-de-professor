/**
 * Canal Educação v3.0 — App JavaScript
 * Authentication, user profile, toast notifications, utilities.
 */

// ─── Auth Helpers ───────────────────────────────────────────────────

function getToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

async function loadUserProfile() {
    const token = getToken();
    if (!token) return;

    try {
        const res = await fetch('/api/v1/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            logout();
            return;
        }

        const user = await res.json();
        localStorage.setItem('user', JSON.stringify(user));

        const nameEl = document.getElementById('user-name');
        const roleEl = document.getElementById('user-role');
        if (nameEl) nameEl.textContent = user.full_name;
        if (roleEl) roleEl.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);

        // Hide admin nav if not admin/gestor
        const adminNav = document.getElementById('nav-admin');
        if (adminNav && !['admin', 'gestor'].includes(user.role)) {
            adminNav.style.display = 'none';
        }
    } catch (e) {
        console.error('Failed to load profile:', e);
    }
}

// ─── Toast Notifications ────────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── API Helpers ────────────────────────────────────────────────────

async function apiGet(url) {
    const token = getToken();
    const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.status === 401) { logout(); return null; }
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

async function apiPost(url, body) {
    const token = getToken();
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });
    if (res.status === 401) { logout(); return null; }
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `API error: ${res.status}`);
    }
    return res.json();
}

async function apiPatch(url, body = {}) {
    const token = getToken();
    const res = await fetch(url, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });
    if (res.status === 401) { logout(); return null; }
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `API error: ${res.status}`);
    }
    return res.json();
}
