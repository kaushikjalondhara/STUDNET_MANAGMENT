/**
 * student.js — Student portal page logic
 */

const STUDENT_DATE_KEY = 'student_selected_attendance_date';
let studentCachedAttendanceRecords = [];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getTodayIsoDate() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatDisplayDate(isoDate) {
  if (!isoDate || typeof isoDate !== 'string') return '—';
  const parts = isoDate.split('-');
  if (parts.length === 3) {
    // Return DD-MM-YYYY
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return isoDate;
}

function getStoredStudentDate() {
  const saved = localStorage.getItem(STUDENT_DATE_KEY);
  return saved || getTodayIsoDate();
}

function setStoredStudentDate(isoDate) {
  if (isoDate) {
    localStorage.setItem(STUDENT_DATE_KEY, isoDate);
  }
}

// ─── Monthly Attendance Processor ───────────────────────────────────────────

async function fetchStudentAttendanceData() {
  let records = [];
  let summary = { total: 0, present: 0, absent: 0, attendance_pct: 0, month_days: 30 };

  // 1. Try Backend API first
  const { ok, data } = await Api.myAttendance();
  if (ok && data) {
    records = Array.isArray(data.history) ? data.history : [];
    summary = {
      total: data.total || records.length,
      month_days: data.month_days || 30,
      present: data.present || 0,
      absent: data.absent || 0,
      attendance_pct: data.attendance_pct || 0,
      history: records
    };
  } else {
    // 2. Fallback to LocalStorage client-side calculation
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth(); // 0-indexed
    const daysElapsed = today.getDate();

    let recordMap = {};
    try {
      const currentStudent = JSON.parse(localStorage.getItem('currentStudent') || '{}');
      const allAtt = JSON.parse(localStorage.getItem('attendance') || '[]');
      const studentId = currentStudent.id || currentStudent._id || currentStudent.roll_no;

      if (studentId) {
        allAtt.filter(a => a.student_id == studentId || a.studentId == studentId).forEach(r => {
          recordMap[r.date] = (r.status || '').toLowerCase();
        });
      }
    } catch (e) {
      console.warn('LocalStorage parse error:', e);
    }

    let presentCount = 0;
    records = [];

    // Generate days for the month up to today
    for (let day = daysElapsed; day >= 1; day--) {
      const d = new Date(currentYear, currentMonth, day);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const dayStr = String(d.getDate()).padStart(2, '0');
      const iso = `${y}-${m}-${dayStr}`;

      const status = recordMap[iso] === 'present' ? 'present' : 'absent';
      if (status === 'present') {
        presentCount++;
      }
      records.push({ date: iso, status: status });
    }

    const absentCount = daysElapsed - presentCount;
    const pct = daysElapsed > 0 ? Math.round((presentCount / daysElapsed) * 1000) / 10 : 0;

    summary = {
      total: daysElapsed,
      month_days: new Date(currentYear, currentMonth + 1, 0).getDate(),
      present: presentCount,
      absent: absentCount,
      attendance_pct: pct,
      history: records
    };
  }

  studentCachedAttendanceRecords = records;
  return summary;
}

// ─── Update Attendance Status on Selected Date ───────────────────────────────

function renderSelectedDateStatus(selectedIsoDate) {
  const dateInput = document.getElementById('studentAttDate');
  const displayDateEl = document.getElementById('displaySelectedDate');
  const badgeEl = document.getElementById('dateAttStatusBadge');

  if (dateInput && dateInput.value !== selectedIsoDate) {
    dateInput.value = selectedIsoDate;
  }

  const formattedDisplay = formatDisplayDate(selectedIsoDate);
  if (displayDateEl) {
    displayDateEl.textContent = formattedDisplay;
  }

  if (!badgeEl) return;

  // Search in cached attendance records
  const match = studentCachedAttendanceRecords.find(r => r.date === selectedIsoDate);

  if (match && (match.status || '').toLowerCase() === 'present') {
    badgeEl.className = 'badge badge-success';
    badgeEl.style.fontSize = '13px';
    badgeEl.style.padding = '5px 14px';
    badgeEl.textContent = '✅ Present';
  } else {
    // If marked absent or attendance was not taken -> Counted as ABSENT
    badgeEl.className = 'badge badge-danger';
    badgeEl.style.fontSize = '13px';
    badgeEl.style.padding = '5px 14px';
    badgeEl.textContent = '❌ Absent';
  }
}

function onStudentDateChange(newIsoDate) {
  if (!newIsoDate) {
    newIsoDate = getTodayIsoDate();
  }
  setStoredStudentDate(newIsoDate);
  renderSelectedDateStatus(newIsoDate);
}

// ─── Dashboard Initialization ────────────────────────────────────────────────

async function initStudentDashboard() {
  if (!Auth.requireStudent()) return;
  Auth.populateStudentUI();

  const user = Auth.getUser();
  if (user) {
    setElS('studentStd',  `Standard ${user.standard || '—'}`);
    setElS('studentRoll', user.roll_no || '—');
    setElS('stdBanner',   `Standard ${user.standard || '—'}`);
  }

  // Load monthly attendance data
  const attData = await fetchStudentAttendanceData();
  setElS('attTotal',   attData.total);
  setElS('attPresent', attData.present);
  setElS('attAbsent',  attData.absent);
  setElS('attPct',     attData.attendance_pct + '%');
  setElS('attPct2',    attData.attendance_pct + '%');

  const bar = document.getElementById('attBar');
  if (bar) bar.style.width = attData.attendance_pct + '%';

  // Initialize Date Picker & Status with saved localStorage date or today
  const selectedDate = getStoredStudentDate();
  renderSelectedDateStatus(selectedDate);

  // Load results summary
  const resRes = await Api.myResults();
  if (resRes.ok && resRes.data) {
    setElS('resultCount', resRes.data.results?.length || 0);
    setElS('avgScore',    (resRes.data.average_score || 0) + '%');
  }
}

// ─── Profile Initialization ──────────────────────────────────────────────────

async function initStudentProfile() {
  if (!Auth.requireStudent()) return;
  Auth.populateStudentUI();

  const { ok, data } = await Api.myProfile();
  if (!ok || !data) { Toast.error('Failed to load profile.'); return; }

  const s = data.student || {};
  window.myStudentProfile = s;
  setElS('profileName',   s.name || 'Student');
  setElS('profileRoll',   s.roll_no || '—');
  setElS('profileStd',    `Standard ${s.standard || '—'}`);
  setElS('profileStd2',   `Standard ${s.standard || '—'}`);
  setElS('profileMobile', s.mobile || '—');
  setElS('profileEmail',  s.email  || '—');

  const avatarEl = document.getElementById('profileAvatar');
  if (avatarEl) {
    if (s.photo || s.photo_url) {
      avatarEl.innerHTML = `<img src="${s.photo || s.photo_url}" style="width:100%;height:100%;border-radius:50%;object-fit:cover" alt="Student Photo" />`;
    } else if (s.name) {
      avatarEl.textContent = s.name[0].toUpperCase();
    }
  }
}

function openMyIdCard() {
  if (window.myStudentProfile && typeof IdCardHelper !== 'undefined') {
    IdCardHelper.showIdCard(window.myStudentProfile);
  } else if (typeof Api !== 'undefined') {
    Api.myProfile().then(({ ok, data }) => {
      if (ok && data.student) {
        window.myStudentProfile = data.student;
        if (typeof IdCardHelper !== 'undefined') IdCardHelper.showIdCard(data.student);
      } else {
        Toast.error('Profile details not loaded.');
      }
    });
  }
}

async function openMyHallTicket() {
  if (typeof Toast !== 'undefined') Toast.info('Checking Hall Ticket status…');
  let student = window.myStudentProfile;
  if (!student && typeof Api !== 'undefined') {
    const { ok, data } = await Api.myProfile();
    if (ok && data.student) {
      student = data.student;
      window.myStudentProfile = data.student;
    }
  }

  if (!student) {
    if (typeof Toast !== 'undefined') Toast.error('Student details could not be loaded.');
    return;
  }

  const std = student.standard || 1;
  // 1. Fetch standard-wise hall ticket configuration from School Settings
  try {
    const { ok, data } = await Api.getHallTicketConfig(std);
    if (!ok || !data?.config) {
      if (typeof Toast !== 'undefined') Toast.error('Failed to verify hall ticket schedule.');
      return;
    }

    const cfg = data.config;
    // 2. Check if hall ticket is enabled / published for this standard in School Settings
    if (cfg.enabled === false) {
      showHallTicketUnpublishedModal(std);
      return;
    }

    // 3. Allowed! Open official hall ticket with standard-wise schedule and guidelines
    if (typeof IdCardHelper !== 'undefined') {
      IdCardHelper.showHallTicket(student, cfg);
    }
  } catch (err) {
    console.error('Hall ticket load error:', err);
    if (typeof Toast !== 'undefined') Toast.error('Error loading hall ticket.');
  }
}

function showHallTicketUnpublishedModal(std) {
  const modalId = 'htUnpublishedModal_' + Date.now();
  const html = `
    <div id="${modalId}" class="id-card-modal-backdrop" onclick="if(event.target===this) document.getElementById('${modalId}').remove()">
      <div class="id-card-modal-container" style="max-width:480px;text-align:center;padding:28px 24px;background:#fff;border-radius:14px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.2)">
        <div style="font-size:52px;margin-bottom:12px">⚠️</div>
        <h3 style="font-size:18px;font-weight:800;color:#1E293B;margin:0 0 8px">હોલ ટિકિટ હજુ જાહેર કરેલ નથી</h3>
        <div style="font-size:14px;color:#DC2626;font-weight:700;margin-bottom:12px">Hall Ticket Not Published for Standard ${std}</div>
        <p style="font-size:13px;color:#475569;line-height:1.6;margin:0 0 20px">
          તમારા ધોરણ <b>(Standard ${std})</b> માટે હોલ ટિકિટ હજુ સ્કૂલ એડમિનિસ્ટ્રેશન દ્વારા બહાર પાડવામાં આવી નથી.<br/>
          સ્કૂલ સેટિંગ્સમાંથી મંજૂરી અને પરીક્ષા ટાઈમટેબલ જાહેર થયા પછી જ તમે અહીંથી હોલ ટિકિટ ડાઉનલોડ કરી શકશો.
        </p>
        <button class="btn btn-primary" onclick="document.getElementById('${modalId}').remove()" style="min-width:140px;padding:8px 20px;font-weight:700">
          સમજાઈ ગયું (Close)
        </button>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);
  if (typeof IdCardHelper !== 'undefined' && IdCardHelper.injectStyles) {
    IdCardHelper.injectStyles();
  }
}

window.openMyIdCard = openMyIdCard;
window.openMyHallTicket = openMyHallTicket;
window.showHallTicketUnpublishedModal = showHallTicketUnpublishedModal;

// ─── Attendance Page Initialization ──────────────────────────────────────────

async function initStudentAttendance() {
  if (!Auth.requireStudent()) return;
  Auth.populateStudentUI();

  const attData = await fetchStudentAttendanceData();

  setElS('attTotal',   attData.total);
  setElS('attPresent', attData.present);
  setElS('attAbsent',  attData.absent);
  setElS('attPct',     attData.attendance_pct + '%');
  setElS('attPct2',    attData.attendance_pct + '%');

  const bar = document.getElementById('attBar');
  if (bar) bar.style.width = attData.attendance_pct + '%';

  // Render Date Picker on Attendance page
  const selectedDate = getStoredStudentDate();
  renderSelectedDateStatus(selectedDate);

  // Render Monthly History Table
  const tbody = document.getElementById('attHistoryBody');
  if (tbody) {
    if (!attData.history.length) {
      tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#64748B;padding:16px">No attendance records this month.</td></tr>';
    } else {
      tbody.innerHTML = attData.history.map((r, i) => {
        const isPres = (r.status || '').toLowerCase() === 'present';
        const displayDate = formatDisplayDate(r.date);
        return `
          <tr>
            <td style="font-weight:600">${i + 1}</td>
            <td><b>${displayDate}</b></td>
            <td>
              <span class="badge ${isPres ? 'badge-success' : 'badge-danger'}">
                ${isPres ? '✅ Present' : '❌ Absent'}
              </span>
            </td>
          </tr>
        `;
      }).join('');
    }
  }
}

// ─── Results Page Initialization ─────────────────────────────────────────────

async function initStudentResults() {
  if (!Auth.requireStudent()) return;
  Auth.populateStudentUI();

  const { ok, data } = await Api.myResults();
  if (!ok) { Toast.error('Failed to load results.'); return; }

  setElS('avgScore',    (data.average_score || 0) + '%');
  setElS('resultCount', data.results?.length || 0);

  const container = document.getElementById('studentReportsContainer');
  if (!container) return;

  const results = data.results || [];
  if (!results.length) {
    container.innerHTML = `
      <div class="card">
        <div class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>No exam results published yet</h3>
          <p>Your exam marksheets will appear here once created by your teacher.</p>
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = results.map(r => {
    const isPass = r.status === 'Pass';
    const gradeClass = 'grade-' + (r.grade || 'F').replace('+', '-plus');

    const subjectRows = (r.subjects || []).map(s => {
      const pct = s.max_marks ? Math.round(s.marks / s.max_marks * 100) : 0;
      return `
        <tr>
          <td><b>${s.subject}</b></td>
          <td style="text-align:right"><b>${s.marks}</b></td>
          <td style="text-align:right">${s.max_marks}</td>
          <td style="text-align:right">${pct}%</td>
          <td style="text-align:center">
            <span class="badge ${pct >= 35 ? 'badge-success' : 'badge-danger'}" style="font-size:11px">
              ${pct >= 35 ? 'Pass' : 'Fail'}
            </span>
          </td>
        </tr>
      `;
    }).join('');

    return `
      <div class="report-card">
        <div class="report-header">
          <div>
            <h3>📋 ${r.exam_name}</h3>
            <small style="opacity:0.9">Published: ${r.created_at ? formatDisplayDate(r.created_at.split('T')[0]) : 'Recent'}</small>
          </div>
          <div class="report-summary-strip">
            <div><strong>Score:</strong> ${r.total_marks} / ${r.max_total} (${r.percentage}%)</div>
            <div class="grade-pill ${gradeClass}" style="background:#fff;color:#4F46E5;font-weight:800">${r.grade}</div>
            <span class="badge ${isPass ? 'badge-success' : 'badge-danger'}" style="background:#fff;color:${isPass ? '#059669' : '#DC2626'};font-weight:800">${r.status}</span>
          </div>
        </div>

        <div class="table-wrap">
          <table class="sub-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th style="text-align:right">Marks Obtained</th>
                <th style="text-align:right">Max Marks</th>
                <th style="text-align:right">Percentage</th>
                <th style="text-align:center">Status</th>
              </tr>
            </thead>
            <tbody>
              ${subjectRows}
            </tbody>
            <tfoot>
              <tr>
                <td>Grand Total</td>
                <td style="text-align:right">${r.total_marks}</td>
                <td style="text-align:right">${r.max_total}</td>
                <td style="text-align:right">${r.percentage}%</td>
                <td style="text-align:center"><span class="badge ${isPass ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    `;
  }).join('');
}

function setElS(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val !== undefined && val !== null ? val : '—';
}
