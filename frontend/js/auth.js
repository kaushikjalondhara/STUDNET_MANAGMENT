/**
 * auth.js — Authentication guard utilities
 * localStorage keys: sms_token, sms_user
 */

const Auth = {
  TOKEN_KEY: 'sms_token',
  USER_KEY:  'sms_user',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem(this.USER_KEY));
    } catch {
      return null;
    }
  },

  isLoggedIn() {
    const token = this.getToken();
    if (!token) return false;
    // Check expiry from JWT payload (no signature verification — that's the server's job)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return Date.now() / 1000 < payload.exp;
    } catch {
      return false;
    }
  },

  isTeacher() {
    const user = this.getUser();
    return user && user.role === 'teacher';
  },

  isStudent() {
    const user = this.getUser();
    return user && user.role === 'student';
  },

  /**
   * Require teacher auth. Redirects to teacher login if not authenticated.
   * Call at the top of every teacher page script.
   */
  requireTeacher() {
    if (!this.isLoggedIn() || !this.isTeacher()) {
      window.location.href = '/teacher/login.html';
      return false;
    }
    return true;
  },

  /**
   * Require student auth. Redirects to student login if not authenticated.
   */
  requireStudent() {
    if (!this.isLoggedIn() || !this.isStudent()) {
      window.location.href = '/student/login.html';
      return false;
    }
    return true;
  },

  /**
   * Save login credentials to localStorage after successful login.
   */
  saveTeacherSession(token, teacher) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify({ ...teacher, role: 'teacher' }));
  },

  saveStudentSession(token, student) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify({ ...student, role: 'student' }));
  },

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(Standard.KEY);
    window.location.href = '/index.html';
  },

  logoutStudent() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = '/student/login.html';
  },

  /**
   * Populate teacher name in sidebar footer.
   */
  populateTeacherUI() {
    const user = this.getUser();
    if (!user) return;
    const nameEl = document.getElementById('teacherName');
    const initEl = document.getElementById('teacherInitial');
    if (nameEl) nameEl.textContent = user.name || 'Teacher';
    if (initEl) initEl.textContent = (user.name || 'T')[0].toUpperCase();
  },

  populateStudentUI() {
    const user = this.getUser();
    if (!user) return;
    const nameEl = document.getElementById('studentName');
    const initEl = document.getElementById('studentInitial');
    if (nameEl) nameEl.textContent = user.name || 'Student';
    if (initEl) initEl.textContent = (user.name || 'S')[0].toUpperCase();
  },

  openSchoolSettingsModal() {
    const existingToken = sessionStorage.getItem('sms_mgmt_token');
    if (existingToken) {
      window.location.href = 'settings.html';
      return;
    }

    let modal = document.getElementById('globalMgmtPasswordModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'globalMgmtPasswordModal';
      modal.className = 'modal-overlay open';
      modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.65);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:9999;';
      modal.innerHTML = `
        <div class="modal" style="background:#fff;border-radius:14px;padding:22px 24px;max-width:420px;width:92%;box-shadow:0 20px 25px -5px rgba(0,0,0,0.25);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div style="display:flex;align-items:center;gap:10px">
              <span style="font-size:24px">🔐</span>
              <div>
                <h3 style="margin:0;font-size:16px;color:#1E293B">Management Authorization</h3>
                <div style="font-size:11.5px;color:#64748B">Enter Master Password to access School Settings</div>
              </div>
            </div>
            <button class="btn btn-outline btn-sm" onclick="Auth.closeSchoolSettingsModal()" style="border:none;font-size:18px;cursor:pointer">✕</button>
          </div>
          <div id="globalMgmtAlert" style="display:none;background:#FEE2E2;color:#991B1B;padding:8px 12px;border-radius:6px;font-size:12px;margin-bottom:12px;font-weight:600"></div>
          <form onsubmit="Auth.submitSchoolSettingsPassword(event)">
            <div style="margin-bottom:14px">
              <label style="display:block;font-size:12px;font-weight:600;color:#475569;margin-bottom:6px">Master Management Password</label>
              <input type="password" id="globalMgmtPasswordInput" class="form-control" placeholder="Enter Management Password (admin123)" required style="width:100%;box-sizing:border-box;padding:8px 12px;font-size:14px;border:1.5px solid #CBD5E1;border-radius:8px;outline:none;">
            </div>
            <div style="display:flex;justify-content:flex-end;gap:8px">
              <button type="button" class="btn btn-outline" onclick="Auth.closeSchoolSettingsModal()">Cancel</button>
              <button type="submit" class="btn btn-primary" id="globalMgmtSubmitBtn" style="background:#4F46E5;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:600;cursor:pointer">🔓 Unlock Settings</button>
            </div>
          </form>
        </div>
      `;
      document.body.appendChild(modal);
    } else {
      modal.style.display = 'flex';
    }
    const input = document.getElementById('globalMgmtPasswordInput');
    const alertEl = document.getElementById('globalMgmtAlert');
    if (alertEl) alertEl.style.display = 'none';
    if (input) {
      input.value = '';
      setTimeout(() => input.focus(), 150);
    }
  },

  closeSchoolSettingsModal() {
    const modal = document.getElementById('globalMgmtPasswordModal');
    if (modal) modal.style.display = 'none';
  },

  async submitSchoolSettingsPassword(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('globalMgmtPasswordInput');
    const alertEl = document.getElementById('globalMgmtAlert');
    const btn = document.getElementById('globalMgmtSubmitBtn');
    const pw = input ? input.value.trim() : '';
    if (!pw) return;

    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Verifying…';
    }
    if (alertEl) alertEl.style.display = 'none';

    try {
      const { ok, data } = await Api.verifyManagementPassword(pw);
      if (btn) {
        btn.disabled = false;
        btn.textContent = '🔓 Unlock Settings';
      }

      if (ok && data?.management_token) {
        sessionStorage.setItem('sms_mgmt_token', data.management_token);
        Toast.success('Management authorized! Opening School Settings…');
        Auth.closeSchoolSettingsModal();
        setTimeout(() => {
          window.location.href = 'settings.html';
        }, 300);
      } else {
        if (alertEl) {
          alertEl.textContent = data?.error || 'Incorrect Management Password (admin123)';
          alertEl.style.display = 'block';
        }
        if (input) {
          input.value = '';
          input.focus();
        }
      }
    } catch (err) {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '🔓 Unlock Settings';
      }
      if (alertEl) {
        alertEl.textContent = 'Error connecting to server.';
        alertEl.style.display = 'block';
      }
    }
  }
};

// Toast notifications (global)
const Toast = {
  container: null,

  _ensure() {
    if (!this.container) {
      this.container = document.getElementById('toast-container');
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        document.body.appendChild(this.container);
      }
    }
  },

  show(message, type = 'info', duration = 3500) {
    this._ensure();
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slideIn .25s ease reverse';
      setTimeout(() => toast.remove(), 240);
    }, duration);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg)   { this.show(msg, 'error'); },
  warning(msg) { this.show(msg, 'warning'); },
  info(msg)    { this.show(msg, 'info'); }
};

// ─── Universal Mobile Navigation ──────────────────────────────────────────────
function initMobileNavigation() {
  const sidebar = document.querySelector('.sidebar');
  const topHeader = document.querySelector('.top-header');
  if (!sidebar) return;

  // 1. Ensure backdrop exists
  let backdrop = document.querySelector('.sidebar-backdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(backdrop);
  }

  // 2. Add mobile toggle button to top-header if not present
  if (topHeader && !topHeader.querySelector('.mobile-nav-toggle')) {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'mobile-nav-toggle';
    toggleBtn.type = 'button';
    toggleBtn.innerHTML = '☰';
    toggleBtn.setAttribute('aria-label', 'Toggle navigation menu');

    const headerLeft = topHeader.querySelector('.header-left');
    if (headerLeft) {
      headerLeft.prepend(toggleBtn);
    } else {
      topHeader.prepend(toggleBtn);
    }

    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
      backdrop.classList.toggle('open');
    });
  }

  // 3. Add explicit close button inside sidebar header
  const sidebarLogo = sidebar.querySelector('.sidebar-logo');
  if (sidebarLogo && !sidebarLogo.querySelector('.sidebar-close-btn')) {
    const closeBtn = document.createElement('button');
    closeBtn.className = 'sidebar-close-btn';
    closeBtn.type = 'button';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', 'Close navigation menu');
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.remove('open');
      backdrop.classList.remove('open');
    });
    sidebarLogo.appendChild(closeBtn);
  }

  // 4. Dismiss on backdrop click
  backdrop.addEventListener('click', () => {
    sidebar.classList.remove('open');
    backdrop.classList.remove('open');
  });

  // 5. Dismiss on nav-link click
  sidebar.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('open');
    });
  });

  // 6. Dismiss on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      backdrop.classList.remove('open');
    }
  });
}

// ─── Universal Notification Bell for Student Header ──────────────────────────
async function initNotificationBell() {
  if (!Auth.isStudent()) return;
  const topHeader = document.querySelector('.top-header');
  if (!topHeader) return;

  let headerRight = topHeader.querySelector('.header-right');
  if (!headerRight) {
    headerRight = document.createElement('div');
    headerRight.className = 'header-right';
    topHeader.appendChild(headerRight);
  }

  if (!headerRight.querySelector('.notif-bell-link')) {
    const bellLink = document.createElement('a');
    bellLink.href = 'notifications.html';
    bellLink.className = 'notif-bell-link';
    bellLink.style.position = 'relative';
    bellLink.style.display = 'inline-flex';
    bellLink.style.alignItems = 'center';
    bellLink.style.justifyContent = 'center';
    bellLink.style.width = '38px';
    bellLink.style.height = '38px';
    bellLink.style.borderRadius = '50%';
    bellLink.style.background = '#F1F5F9';
    bellLink.style.fontSize = '18px';
    bellLink.style.color = '#1E293B';
    bellLink.title = 'View Notifications';
    bellLink.innerHTML = '🔔<span class="notif-badge" style="display:none;position:absolute;top:-2px;right:-2px;background:#EF4444;color:#fff;font-size:10px;font-weight:800;padding:2px 6px;border-radius:10px;line-height:1">0</span>';

    headerRight.prepend(bellLink);

    // Fetch unread count
    if (typeof Api !== 'undefined' && typeof Api.getUnreadNotificationsCount === 'function') {
      try {
        const { ok, data } = await Api.getUnreadNotificationsCount();
        if (ok && data && data.unread_count > 0) {
          const badge = bellLink.querySelector('.notif-badge');
          if (badge) {
            badge.textContent = data.unread_count;
            badge.style.display = 'inline-block';
          }
        }
      } catch (err) {}
    }
  }
}

// ─── Universal School Branding Engine ─────────────────────────────────────────
const SchoolBranding = {
  CACHE_KEY: 'sms_school_branding',

  getStored() {
    try {
      const raw = localStorage.getItem(this.CACHE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  setStored(data) {
    try {
      localStorage.setItem(this.CACHE_KEY, JSON.stringify(data));
    } catch (e) {}
  },

  getName() {
    const stored = this.getStored();
    return (stored && (stored.name || stored.school_name)) || 'gyan jyot vidhaya bhavan';
  },

  apply(info) {
    if (!info) return;
    const name = info.name || info.school_name || '';
    if (!name) return;

    // 1. Update all sidebar logos
    document.querySelectorAll('.sidebar-logo h2').forEach(el => {
      el.textContent = name;
    });

    // 2. Update portal/login headers
    document.querySelectorAll('.portal-header h1, .login-header h1, .select-std-header h1').forEach(el => {
      if (el.classList.contains('preserve-title')) return;
      if (el.textContent.includes('EduManage Pro') || el.closest('.portal-header')) {
        el.textContent = name;
      }
    });

    // 3. Update any explicit class/id elements
    document.querySelectorAll('.school-name-text, .school-official-name, [data-school-name]').forEach(el => {
      el.textContent = name;
    });

    // 4. Update page titles
    if (document.title && document.title.includes('EduManage Pro')) {
      document.title = document.title.replace('EduManage Pro', name);
    }

    // 5. Update footer copyright notices
    document.querySelectorAll('.login-footer, .sidebar-footer-copy').forEach(el => {
      if (el.textContent.includes('EduManage Pro')) {
        el.textContent = el.textContent.replace('EduManage Pro', name);
      }
    });

    // 6. Update receipt and payment payee displays
    const upiPayee = document.getElementById('upiPayeeDisplay');
    if (upiPayee) upiPayee.textContent = name;
    document.querySelectorAll('.receipt-title').forEach(el => {
      el.textContent = name;
    });

    // 7. Dispatch event for modules (fees, timetable, etc.) that need latest settings
    window.dispatchEvent(new CustomEvent('schoolBrandingLoaded', { detail: info }));
  },

  async sync() {
    // 1. Apply cached branding immediately (0ms instant paint)
    const cached = this.getStored();
    if (cached) {
      this.apply(cached);
    }

    // 2. Refresh from server in background
    if (typeof Api !== 'undefined' && typeof Api.getPublicSchoolInfo === 'function') {
      try {
        const { ok, data } = await Api.getPublicSchoolInfo();
        if (ok && data && data.school_info) {
          const info = {
            ...data.school_info,
            academic_year: data.academic_year || data.school_info.academic_year,
            payment_settings: data.payment_settings || {},
            standard_fees: data.standard_fees || {},
            fee_types: data.fee_types || []
          };
          this.setStored(info);
          this.apply(info);
        }
      } catch (e) {}
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initMobileNavigation();
  initNotificationBell();
  SchoolBranding.sync();
});
if (document.readyState === 'interactive' || document.readyState === 'complete') {
  initMobileNavigation();
  initNotificationBell();
  SchoolBranding.sync();
}

