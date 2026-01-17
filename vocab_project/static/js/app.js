// API Helper Functions
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');

    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    if (token) {
        defaultHeaders['Authorization'] = `Token ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    const response = await fetch(url, config);

    // Handle 401 - Unauthorized
    if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login/';
    }

    return response;
}

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: 'fa-check',
        error: 'fa-times',
        warning: 'fa-exclamation',
        info: 'fa-info'
    };

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${icons[type] || icons.info}"></i>
        </div>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Text-to-Speech
function speakWord(word) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(word);
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        utterance.pitch = 1;

        // Get available voices and prefer US English
        const voices = speechSynthesis.getVoices();
        const usVoice = voices.find(v => v.lang === 'en-US') || voices[0];
        if (usVoice) {
            utterance.voice = usVoice;
        }

        speechSynthesis.speak(utterance);
    } else {
        showToast('Text-to-speech not supported in this browser', 'warning');
    }
}

// Load voices when they become available
if ('speechSynthesis' in window) {
    speechSynthesis.onvoiceschanged = function() {
        speechSynthesis.getVoices();
    };
}

// Sidebar Toggle for Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.querySelector('.menu-toggle');

    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});

// Modal Functions
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// Global Search
document.addEventListener('DOMContentLoaded', function() {
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    window.location.href = `/vocabulary/?search=${encodeURIComponent(query)}`;
                }
            }
        });
    }
});

// Debounce Function for Search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading State Helper
function setLoading(element, isLoading) {
    if (isLoading) {
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
            </div>
        `;
    }
}

// Form Validation Helper
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;

    let isValid = true;
    const errors = {};

    for (const [fieldName, fieldRules] of Object.entries(rules)) {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) continue;

        const value = field.value.trim();

        if (fieldRules.required && !value) {
            errors[fieldName] = `${fieldRules.label || fieldName} is required`;
            isValid = false;
        } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
            errors[fieldName] = `${fieldRules.label || fieldName} must be at least ${fieldRules.minLength} characters`;
            isValid = false;
        } else if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
            errors[fieldName] = fieldRules.message || `Invalid ${fieldRules.label || fieldName}`;
            isValid = false;
        }

        // Update UI
        const errorEl = field.parentElement.querySelector('.form-error');
        if (errors[fieldName]) {
            field.style.borderColor = 'var(--danger)';
            if (errorEl) {
                errorEl.textContent = errors[fieldName];
            }
        } else {
            field.style.borderColor = '';
            if (errorEl) {
                errorEl.textContent = '';
            }
        }
    }

    return isValid;
}

// Check if user is authenticated
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// Get current user
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Check if current user is admin
function isAdmin() {
    const user = getCurrentUser();
    return user && user.role === 'admin';
}

// Logout Function
async function logout() {
    try {
        await apiRequest('/api/auth/logout/', { method: 'POST' });
    } catch (e) {
        // Ignore errors during logout
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login/';
}

// Initialize tooltips (if needed)
function initTooltips() {
    document.querySelectorAll('[title]').forEach(el => {
        // Could add custom tooltip implementation here
    });
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Console welcome message
console.log('%c VocabMaster ', 'background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 10px 20px; font-size: 16px; font-weight: bold; border-radius: 5px;');
console.log('Welcome to VocabMaster - Your English Vocabulary Learning Companion!');
