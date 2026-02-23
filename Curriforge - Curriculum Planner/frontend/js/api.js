/* ═══════════════════════════════════════════
   CurriForge - API Helper & Utilities
   ═══════════════════════════════════════════ */

const API_BASE = '/api';

// ── Token Management ──
function getToken() {
    return localStorage.getItem('curriforge_token');
}

function setToken(token) {
    localStorage.setItem('curriforge_token', token);
}

function setUser(user) {
    localStorage.setItem('curriforge_user', JSON.stringify(user));
}

function getUser() {
    const data = localStorage.getItem('curriforge_user');
    return data ? JSON.parse(data) : null;
}

function logout() {
    localStorage.removeItem('curriforge_token');
    localStorage.removeItem('curriforge_user');
    window.location.href = '/';
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = '/';
        return false;
    }
    return true;
}

// ── API Fetch Wrapper ──
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            logout();
            return null;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ── Toast Notifications ──
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ── Loading Overlay ──
function showLoading(message = 'Loading...') {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.loading-text').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) overlay.remove();
}

// ── Sidebar Setup ──
function setupSidebar(activePage) {
    const user = getUser();
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // Set active nav item
    const navItems = sidebar.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.dataset.page === activePage) {
            item.classList.add('active');
        }
    });

    // Set user info
    if (user) {
        const avatar = sidebar.querySelector('.user-avatar');
        const nameEl = sidebar.querySelector('.user-details .name');
        const emailEl = sidebar.querySelector('.user-details .email');

        if (avatar) avatar.textContent = (user.name || 'U')[0].toUpperCase();
        if (nameEl) nameEl.textContent = user.name || 'User';
        if (emailEl) emailEl.textContent = user.email || '';
    }

    // Mobile menu
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
}

// ── Chart Helper (using Chart.js) ──
function createLearningChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Score (%)',
                data: data.scores || [],
                borderColor: '#6C63FF',
                backgroundColor: 'rgba(108, 99, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#6C63FF',
                pointBorderColor: '#fff',
                pointRadius: 5,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#A7A9BE' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(46, 46, 74, 0.5)' },
                    ticks: { color: '#A7A9BE' },
                },
                x: {
                    grid: { color: 'rgba(46, 46, 74, 0.3)' },
                    ticks: { color: '#A7A9BE' },
                }
            }
        }
    });
}

// ── Utility Functions ──
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Simple markdown to HTML for AI responses
function markdownToHtml(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
}
