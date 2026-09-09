/**
 * attendance.js — Full date-wise attendance management
 */

let attendanceData   = [];      // Current date's attendance list
let currentDate      = '';      // Currently loaded date (YYYY-MM-DD)
let historySortOrder = 'asc';   // 'asc' so history starts from 1st of month

// ─── Init ─────────────────────────────────────────────────────────────────────

async function initAttendance() {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  // Set today as default date
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('attendanceDate');
  if (dateInput) dateInput.value = today;

  // Set current month in history month picker
  const monthInput = document.getElementById('historyMonth');
  if (monthInput) monthInput.value = today.slice(0, 7);

  // Load attendance for today + history
  await Promise.all([
    loadAttendance(today),
    loadHistory()
  ]);

  // Enable fast & smooth independent wheel scrolling
  initSheetFastScroll();
}

// ─── Load attendance for a specific date ─────────────────────────────────────

async function loadAttendance(dateStr) {
  if (!dateStr) {
    dateStr = document.getElementById('attendanceDate').value;
  }
  currentDate = dateStr;

  const std   = Standard.getActive();
  const tbody = document.getElementById('attendanceBody');
  const noAttEl  = document.getElementById('noAttMsg');
  const attTable = document.getElementById('attTable');

  if (tbody) tbody.innerHTML = `<tr><td colspan="4">
    <div class="loading-overlay"><div class="spinner"></div></div></td></tr>`;
  if (noAttEl)  noAttEl.style.display  = 'none';
  if (attTable) attTable.style.display = 'table';

  const { ok, data } = await Api.getAttendance(std, dateStr);
  if (!ok) {
    Toast.error(data.error || 'Failed to load attendance.');
    return;
  }

  attendanceData = data.attendance || [];
  const summary  = data.summary  || {};

  // Update date display
  const loadedDateEl = document.getElementById('loadedDate');
  if (loadedDateEl) loadedDateEl.textContent = formatDate(dateStr);

  // If attendance was never saved for this date → show notice
  if (!data.has_records) {
    showNoAttMsg(dateStr, false);
  } else {
    if (noAttEl) noAttEl.style.display = 'none';
  }

  renderAttendance(attendanceData);
  updateSummary(summary);

  // Highlight active row in history table if present
  document.querySelectorAll('.history-row').forEach(r => r.classList.remove('selected-row'));
  const activeRow = document.getElementById(`hrow_${dateStr}`);
  if (activeRow) activeRow.classList.add('selected-row');
}

function showNoAttMsg(dateStr, hideTable = true) {
  const noAttEl  = document.getElementById('noAttMsg');
  const noAttDate = document.getElementById('noAttDate');
  if (noAttEl) {
    noAttEl.style.display = 'flex';
    if (noAttDate) noAttDate.textContent = formatDate(dateStr);
  }
  // Don't hide the table — let teacher mark fresh attendance
}

// ─── Render attendance table ──────────────────────────────────────────────────

function renderAttendance(records) {
  const tbody = document.getElementById('attendanceBody');
  if (!tbody) return;

  setEl('studentCountBadge', `${records.length} Students`);

  if (!records.length) {
    tbody.innerHTML = `<tr><td colspan="4">
      <div class="empty-state">
        <div class="empty-icon">👨‍🎓</div>
        <h3>No students in this standard</h3>
      </div></td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
    const isPres = r.status === 'present';
    const isAbs  = r.status === 'absent';
    return `
    <tr data-id="${r.student_id}">
      <td style="font-weight:600">${r.roll_no}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="student-avatar-sm">${r.name[0].toUpperCase()}</div>
          ${r.name}
        </div>
      </td>
      <td>
        <div class="att-toggle">
          <button class="att-btn present ${isPres ? 'active' : ''}"
            onclick="markAttendance('${r.student_id}', 'present', this)">✅ Present</button>
          <button class="att-btn absent ${isAbs ? 'active' : ''}"
            onclick="markAttendance('${r.student_id}', 'absent', this)">❌ Absent</button>
        </div>
      </td>
      <td>
        <span class="badge ${isPres ? 'badge-success' : isAbs ? 'badge-danger' : 'badge-gray'}" id="badge_${r.student_id}">
          ${r.status === 'not_marked' ? 'Not Marked' : r.status.charAt(0).toUpperCase() + r.status.slice(1)}
        </span>
      </td>
    </tr>`;
  }).join('');
}

function filterAttendanceList() {
  const q = (document.getElementById('attSearchInput')?.value || '').toLowerCase().trim();
  const rows = document.querySelectorAll('#attendanceBody tr[data-id]');
  let visibleCount = 0;
  rows.forEach(r => {
    const text = r.textContent.toLowerCase();
    const match = text.includes(q);
    r.style.display = match ? '' : 'none';
    if (match) visibleCount++;
  });
  const countBadge = document.getElementById('studentCountBadge');
  if (countBadge) {
    countBadge.textContent = q ? `${visibleCount} of ${rows.length}` : `${rows.length} Students`;
  }
}

// ─── Mark individual attendance ───────────────────────────────────────────────

function markAttendance(studentId, status, btn) {
  const record = attendanceData.find(r => r.student_id === studentId);
  if (record) record.status = status;

  // Update buttons
  const row = btn.closest('tr');
  row.querySelectorAll('.att-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  // Update badge
  const badge = document.getElementById(`badge_${studentId}`);
  if (badge) {
    badge.className = `badge ${status === 'present' ? 'badge-success' : 'badge-danger'}`;
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
  }

  // Live summary
  updateSummary({
    total:   attendanceData.length,
    present: attendanceData.filter(r => r.status === 'present').length,
    absent:  attendanceData.filter(r => r.status === 'absent').length,
  });
}

// ─── Mark all present ─────────────────────────────────────────────────────────

// ─── Mark all present / absent ────────────────────────────────────────────────

function markAllPresent() {
  attendanceData.forEach(r => r.status = 'present');
  renderAttendance(attendanceData);
  updateSummary({
    total:   attendanceData.length,
    present: attendanceData.length,
    absent:  0
  });
  const noAttEl = document.getElementById('noAttMsg');
  if (noAttEl) noAttEl.style.display = 'none';
}

function markAllAbsent() {
  attendanceData.forEach(r => r.status = 'absent');
  renderAttendance(attendanceData);
  updateSummary({
    total:   attendanceData.length,
    present: 0,
    absent:  attendanceData.length
  });
  const noAttEl = document.getElementById('noAttMsg');
  if (noAttEl) noAttEl.style.display = 'none';
}

// ─── Update summary counters ──────────────────────────────────────────────────

function updateSummary(s) {
  const total      = s.total   || 0;
  const present    = s.present || 0;
  const absent     = s.absent  || 0;
  const notMarked  = Math.max(0, total - present - absent);
  const pct        = total > 0 ? Math.round(present / total * 100) : 0;

  setEl('summaryTotal',    total);
  setEl('summaryPresent',  present);
  setEl('summaryAbsent',   absent);
  setEl('summaryNotMarked', notMarked);
  setEl('attendancePct',   pct + '%');

  const bar = document.getElementById('attBar');
  if (bar) bar.style.width = pct + '%';

  // Colour the pct badge
  const pctEl = document.getElementById('attendancePct');
  if (pctEl) {
    pctEl.style.color = pct >= 75 ? '#059669' : pct >= 50 ? '#D97706' : '#DC2626';
  }
}

// ─── Save attendance ──────────────────────────────────────────────────────────

async function saveAttendance() {
  const std = Standard.getActive();
  const dateStr = currentDate || document.getElementById('attendanceDate').value;

  const records = attendanceData
    .filter(r => r.status !== 'not_marked')
    .map(r => ({ student_id: r.student_id, status: r.status }));

  if (!records.length) {
    Toast.warning('Please mark at least one student before saving.');
    return;
  }

  const btn = document.getElementById('saveBtn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Saving…'; }

  const { ok, data } = await Api.saveAttendance(std, dateStr, records);

  if (btn) { btn.disabled = false; btn.textContent = '💾 Save Attendance'; }

  if (ok) {
    Toast.success(data.message || `Attendance saved for ${formatDate(dateStr)}!`);
    // Refresh the history panel
    await loadHistory();
    // Hide the "no records" notice since we just saved
    const noAttEl = document.getElementById('noAttMsg');
    if (noAttEl) noAttEl.style.display = 'none';
  } else {
    Toast.error(data.error || 'Failed to save attendance.');
  }
}

// ─── Load date picker and attendance ─────────────────────────────────────────

function onDateChange() {
  const dateInput = document.getElementById('attendanceDate');
  if (dateInput && dateInput.value) {
    loadAttendance(dateInput.value);
  }
}

// ─── History Sorting and Month Navigation ────────────────────────────────────

function toggleSortOrder() {
  historySortOrder = historySortOrder === 'asc' ? 'desc' : 'asc';
  const btn = document.getElementById('btnSortOrder');
  if (btn) {
    btn.textContent = historySortOrder === 'asc' ? '⬆️ 1st → End' : '⬇️ End → 1st';
  }
  loadHistory();
}

// ─── Load History ─────────────────────────────────────────────────────────────

async function loadHistory() {
  const std = Standard.getActive();
  const monthInput = document.getElementById('historyMonth');
  const month = monthInput?.value || new Date().toISOString().slice(0, 7);

  // Update badge in history header
  const monthBadge = document.getElementById('historyMonthBadge');
  if (monthBadge && month) {
    const [y, m] = month.split('-');
    const mNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    monthBadge.textContent = `${mNames[parseInt(m, 10) - 1]} ${y}`;
  }

  const { ok, data } = await Api.get(`/attendance/history?standard=${std}&month=${month}&sort=${historySortOrder}`);
  if (!ok) return;
  renderHistory(data.history || []);
}

function renderHistory(history) {
  const container = document.getElementById('historyBody');
  if (!container) return;

  if (!history.length) {
    container.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:#94A3B8">
      No attendance data for this period.</td></tr>`;
    return;
  }

  container.innerHTML = history.map(h => {
    const pct = h.attendance_pct;
    const color = pct >= 75 ? '#059669' : pct >= 50 ? '#D97706' : '#DC2626';
    const isSelected = (h.date === currentDate);
    const todayBadge = h.is_today ? `<span class="today-tag">Today</span>` : '';

    let statusBadge = '';
    let presDisplay = '';
    let absDisplay  = '';
    let pctDisplay  = '';

    if (h.is_future && !h.is_marked) {
      statusBadge = `<span class="badge" style="background:#F1F5F9;color:#64748B;font-size:10px">⏳ Upcoming</span>`;
      presDisplay = `<span style="color:#94A3B8">—</span>`;
      absDisplay  = `<span style="color:#94A3B8">—</span>`;
      pctDisplay  = `<span style="color:#94A3B8">—</span>`;
    } else if (h.is_marked) {
      statusBadge = `<span class="badge badge-success" style="font-size:10px">✅ Marked</span>`;
      presDisplay = `<span class="badge badge-success">✅ ${h.present}</span>`;
      absDisplay  = `<span class="badge badge-danger">❌ ${h.absent}</span>`;
      pctDisplay  = `<strong style="color:${color}">${pct}%</strong>`;
    } else {
      // Past or today not marked: "attendence lidhi na hoy to e bdha absent pn hestory akha month ni1 date thi avvioye"
      statusBadge = `<span class="badge" style="background:#FEE2E2;color:#991B1B;font-size:10px">❌ All Absent</span>`;
      presDisplay = `<span style="color:#64748B">0</span>`;
      absDisplay  = `<span class="badge badge-danger">❌ ${h.absent}</span>`;
      pctDisplay  = `<strong style="color:#DC2626">0%</strong>`;
    }

    return `
    <tr class="history-row ${isSelected ? 'selected-row' : ''}" id="hrow_${h.date}" onclick="selectHistoryDate('${h.date}')" style="cursor:pointer">
      <td>
        <button class="date-btn" onclick="selectHistoryDate('${h.date}'); event.stopPropagation()">
          📅 ${formatDate(h.date)}
        </button>
        ${todayBadge}
      </td>
      <td>${presDisplay}</td>
      <td>${absDisplay}</td>
      <td>${h.total}</td>
      <td>${pctDisplay}</td>
      <td>${statusBadge}</td>
    </tr>`;
  }).join('');
}

function selectHistoryDate(dateStr) {
  // Update the date picker
  const dateInput = document.getElementById('attendanceDate');
  if (dateInput) dateInput.value = dateStr;

  // Highlight the selected row
  document.querySelectorAll('.history-row').forEach(r => r.classList.remove('selected-row'));
  const row = document.getElementById(`hrow_${dateStr}`);
  if (row) row.classList.add('selected-row');

  // Load attendance for that date
  loadAttendance(dateStr);

  // Reset inner sheet scroll to top smoothly without moving the window/header
  const sheetWrap = document.querySelector('.attendance-sheet-wrap');
  if (sheetWrap) sheetWrap.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── Fast & Independent Sheet Scrolling ──────────────────────────────────────

function initSheetFastScroll() {
  const sheetWrap = document.querySelector('.attendance-sheet-wrap');
  if (sheetWrap && !sheetWrap._hasFastScroll) {
    sheetWrap._hasFastScroll = true;
    sheetWrap.addEventListener('wheel', (e) => {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        e.preventDefault();
        sheetWrap.scrollTop += e.deltaY * 1.75;
      }
    }, { passive: false });
  }

  const histWrap = document.querySelector('.history-sheet-wrap');
  if (histWrap && !histWrap._hasFastScroll) {
    histWrap._hasFastScroll = true;
    histWrap.addEventListener('wheel', (e) => {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        e.preventDefault();
        histWrap.scrollTop += e.deltaY * 1.75;
      }
    }, { passive: false });
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(isoDate) {
  if (!isoDate) return '—';
  const [y, m, d] = isoDate.split('-');
  return `${d}-${m}-${y}`;
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
