/**
 * teacher.js — Teacher dashboard, students, add/edit pages
 */

// ─── Dashboard ────────────────────────────────────────────────────────────────

let currentTeacherDashboardDate = new Date().toISOString().split('T')[0];

function updateDashboardDateDisplay(dateStr) {
  const currentDateEl = document.getElementById('currentDate');
  if (!currentDateEl) return;
  try {
    if (!dateStr) {
      const dateInput = document.getElementById('dashboardDate');
      dateStr = (dateInput && dateInput.value) ? dateInput.value : new Date().toISOString().split('T')[0];
    }
    const [y, m, d] = dateStr.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    currentDateEl.textContent = dateObj.toLocaleDateString('en-IN', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  } catch (e) {
    currentDateEl.textContent = dateStr;
  }
}

async function loadDashboard(customDate) {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  if (customDate) {
    currentTeacherDashboardDate = customDate;
  } else {
    const dateInput = document.getElementById('dashboardDate');
    currentTeacherDashboardDate = (dateInput && dateInput.value) ? dateInput.value : new Date().toISOString().split('T')[0];
  }

  const dateInput = document.getElementById('dashboardDate');
  if (dateInput && dateInput.value !== currentTeacherDashboardDate) {
    dateInput.value = currentTeacherDashboardDate;
  }

  updateDashboardDateDisplay(currentTeacherDashboardDate);

  const std = Standard.getActive();
  const { ok, data } = await Api.getDashboard(std, currentTeacherDashboardDate);
  if (!ok) { Toast.error(data?.error || 'Failed to load dashboard.'); return; }

  const s = data.stats;
  setEl('totalStudents',   s.total_students);
  setEl('presentToday',    s.present_today);
  setEl('absentToday',     s.absent_today);
  setEl('notMarked',       s.not_marked);
  setEl('attendancePct',   s.attendance_pct + '%');
  setEl('classAverage',    s.class_average + '%');

  const bar = document.getElementById('attendanceBar');
  if (bar) bar.style.width = s.attendance_pct + '%';
}

function onDashboardDateChange(newDate) {
  if (!newDate) newDate = new Date().toISOString().split('T')[0];
  updateDashboardDateDisplay(newDate);
  loadDashboard(newDate);
}

// ─── Students List ────────────────────────────────────────────────────────────

async function loadStudents() {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  const std = Standard.getActive();
  const tbody = document.getElementById('studentsBody');
  const countEl = document.getElementById('studentCount');
  if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="loading-overlay"><div class="spinner"></div></div></td></tr>';

  const { ok, data } = await Api.getStudents(std);
  if (!ok) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:#DC2626">
      <div style="font-size:24px;margin-bottom:6px">⚠️</div>
      <div style="font-weight:700;font-size:14px">${data.error || 'Failed to load students.'}</div>
      <div style="font-size:12px;color:#64748B;margin-top:4px">Make sure the Flask backend is running on port 5000</div>
      <button class="btn btn-primary btn-sm" onclick="loadStudents()" style="margin-top:12px">🔄 Retry</button>
    </td></tr>`;
    Toast.error(data.error || 'Failed to load students.');
    return;
  }

  const students = data.students || [];
  window.cachedStudentsList = students;
  if (countEl) countEl.textContent = students.length;

  if (!students.length) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">👨‍🎓</div><h3>No students enrolled</h3><p>Add a student to Standard ${std}</p></div></td></tr>`;
    return;
  }

  renderStudentsTable(students, tbody);
  setupStudentSearch(students, tbody);
}

function renderStudentsTable(students, tbody) {
  if (!tbody) return;
  tbody.innerHTML = students.map((s, i) => {
    const pw = s.password || 'student123';
    return `
    <tr data-id="${s._id}" data-name="${s.name.toLowerCase()}">
      <td>${i + 1}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="student-avatar-sm">${s.name[0].toUpperCase()}</div>
          <strong>${s.name}</strong>
        </div>
      </td>
      <td>${s.roll_no}</td>
      <td>${s.email || '—'}</td>
      <td><strong>${s.mobile || s.phone || '—'}</strong></td>
      <td>
        <div style="display:inline-flex;align-items:center;gap:6px;background:#F8FAFC;padding:4px 8px;border-radius:6px;border:1px solid #E2E8F0">
          <span id="pw-txt-${s._id}" data-pw="${pw}" data-shown="false" style="font-family:monospace;font-size:13px;letter-spacing:1px;color:#334155;min-width:60px;display:inline-block">••••••</span>
          <button type="button" class="btn btn-outline btn-sm" onclick="toggleDirectoryPw('${s._id}')" id="pw-btn-${s._id}" title="Show / Hide Password" style="padding:2px 6px;font-size:11px;line-height:1">👁️</button>
          <button type="button" class="btn btn-outline btn-sm" onclick="copyStudentPw('${s._id}')" title="Copy Password" style="padding:2px 6px;font-size:11px;line-height:1">📋</button>
        </div>
      </td>
      <td>
        <div style="display:flex;gap:5px;flex-wrap:wrap">
          <button type="button" class="btn btn-outline btn-sm" onclick="showStudentIdCard('${s._id}')" title="Print Student ID Card" style="padding:3px 7px;font-size:11px">🪪 ID</button>
          <button type="button" class="btn btn-outline btn-sm" onclick="showStudentHallTicket('${s._id}')" title="Print Exam Hall Ticket" style="padding:3px 7px;font-size:11px">🎫 Ticket</button>
          <a href="edit-student.html?id=${s._id}" class="btn btn-outline btn-sm" style="padding:3px 7px;font-size:11px">✏️</a>
          <button class="btn btn-danger btn-sm" onclick="deleteStudent('${s._id}','${s.name}')" style="padding:3px 7px;font-size:11px">🗑️</button>
        </div>
      </td>
    </tr>
  `;
  }).join('');
}

function showStudentIdCard(studentId) {
  const s = (window.cachedStudentsList || []).find(item => String(item._id) === String(studentId));
  if (s && typeof IdCardHelper !== 'undefined') {
    IdCardHelper.showIdCard(s);
  } else {
    Toast.error('Student details not found.');
  }
}

function showStudentHallTicket(studentId) {
  const s = (window.cachedStudentsList || []).find(item => String(item._id) === String(studentId));
  if (s && typeof IdCardHelper !== 'undefined') {
    IdCardHelper.showHallTicket(s);
  } else {
    Toast.error('Student details not found.');
  }
}

function toggleDirectoryPw(studentId) {
  const txtEl = document.getElementById(`pw-txt-${studentId}`);
  const btnEl = document.getElementById(`pw-btn-${studentId}`);
  if (!txtEl) return;
  const isShown = txtEl.dataset.shown === 'true';
  if (isShown) {
    txtEl.textContent = '••••••';
    txtEl.dataset.shown = 'false';
    if (btnEl) btnEl.textContent = '👁️';
  } else {
    txtEl.textContent = txtEl.dataset.pw;
    txtEl.dataset.shown = 'true';
    if (btnEl) btnEl.textContent = '🙈';
  }
}

function copyStudentPw(studentId) {
  const txtEl = document.getElementById(`pw-txt-${studentId}`);
  const pw = txtEl ? txtEl.dataset.pw : '';
  if (!pw) return;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(pw).then(() => {
      Toast.success('Password copied: ' + pw);
    }).catch(() => {
      fallbackCopy(pw);
    });
  } else {
    fallbackCopy(pw);
  }
}

function fallbackCopy(text) {
  const input = document.createElement('input');
  input.value = text;
  document.body.appendChild(input);
  input.select();
  document.execCommand('copy');
  document.body.removeChild(input);
  Toast.success('Password copied: ' + text);
}

function setupStudentSearch(students, tbody) {
  const searchInput = document.getElementById('searchInput');
  if (!searchInput) return;
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    const filtered = students.filter(s =>
      s.name.toLowerCase().includes(q) ||
      String(s.roll_no).includes(q) ||
      (s.mobile || '').toLowerCase().includes(q) ||
      (s.email || '').toLowerCase().includes(q)
    );
    renderStudentsTable(filtered, tbody);
    const countEl = document.getElementById('studentCount');
    if (countEl) countEl.textContent = filtered.length;
  });
}

async function deleteStudent(id, name) {
  if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
  const { ok, data } = await Api.deleteStudent(id);
  if (ok) {
    Toast.success('Student deleted.');
    loadStudents();
  } else {
    Toast.error(data.error || 'Delete failed.');
  }
}

// ─── Add Student ──────────────────────────────────────────────────────────────

async function initAddStudent() {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  const std = Standard.getActive();
  const stdInput = document.getElementById('standardInput');
  const stdDisplay = document.getElementById('standardDisplay');
  if (stdInput) stdInput.value = std;
  if (stdDisplay) stdDisplay.textContent = `Standard ${std}`;
}

async function submitAddStudent(e) {
  e.preventDefault();
  const form = e.target;
  const std = Standard.getActive();

  const payload = {
    name:     form.name.value.trim(),
    roll_no:  form.roll_no.value,
    standard: std,
    email:    form.email.value.trim(),
    mobile:   form.mobile.value.trim(),
    password: form.password.value
  };

  const btn = form.querySelector('[type=submit]');
  btn.disabled = true;
  btn.textContent = 'Saving…';

  const { ok, data } = await Api.addStudent(payload);
  btn.disabled = false;
  btn.textContent = 'Enroll Student';

  if (ok) {
    Toast.success(`${payload.name} enrolled in Standard ${std}!`);
    setTimeout(() => window.location.href = 'students.html', 1200);
  } else {
    Toast.error(data.error || 'Failed to add student.');
  }
}

// ─── Edit Student ─────────────────────────────────────────────────────────────

async function initEditStudent() {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  if (!id) { window.location.href = 'students.html'; return; }

  const { ok, data } = await Api.getStudent(id);
  if (!ok) { Toast.error('Student not found.'); setTimeout(() => window.location.href = 'students.html', 1500); return; }

  const s = data.student;
  document.getElementById('editStudentId').value = s._id;
  document.getElementById('editName').value       = s.name;
  document.getElementById('editRollNo').value     = s.roll_no;
  document.getElementById('editEmail').value      = s.email  || '';
  document.getElementById('editMobile').value     = s.mobile || '';
  document.getElementById('editStandard').value   = `Standard ${s.standard}`;
  const pwInput = document.getElementById('editPassword');
  if (pwInput) pwInput.value = s.password || 'student123';
}

function toggleEditPasswordVisibility() {
  const pwInput = document.getElementById('editPassword');
  const btn = document.getElementById('toggleEditPwBtn');
  if (!pwInput) return;
  if (pwInput.type === 'password') {
    pwInput.type = 'text';
    if (btn) btn.textContent = '🙈 Hide';
  } else {
    pwInput.type = 'password';
    if (btn) btn.textContent = '👁️ Show';
  }
}

function copyEditPassword() {
  const pwInput = document.getElementById('editPassword');
  if (!pwInput || !pwInput.value) {
    Toast.error('Password is empty.');
    return;
  }
  const pw = pwInput.value;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(pw).then(() => {
      Toast.success('Password copied to clipboard!');
    }).catch(() => {
      fallbackCopy(pw);
    });
  } else {
    fallbackCopy(pw);
  }
}

async function submitEditStudent(e) {
  e.preventDefault();
  const id = document.getElementById('editStudentId').value;
  const payload = {
    name:     document.getElementById('editName').value.trim(),
    roll_no:  document.getElementById('editRollNo').value,
    email:    document.getElementById('editEmail').value.trim(),
    mobile:   document.getElementById('editMobile').value.trim(),
    password: (document.getElementById('editPassword')?.value || '').trim()
  };

  const btn = e.target.querySelector('[type=submit]');
  btn.disabled = true;
  btn.textContent = 'Saving…';

  const { ok, data } = await Api.updateStudent(id, payload);
  btn.disabled = false;
  btn.textContent = 'Save Changes';

  if (ok) {
    Toast.success('Student details and password updated!');
    setTimeout(() => window.location.href = 'students.html', 1200);
  } else {
    Toast.error(data.error || 'Update failed.');
  }
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
