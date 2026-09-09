/**
 * result.js — Complete Student Exam Results Management for Teachers
 */

let allResults = [];
let students   = [];

const DEFAULT_SUBJECTS = [
  'Mathematics',
  'Science',
  'English',
  'Social Science',
  'Gujarati',
  'Hindi'
];

async function initResults() {
  if (!Auth.requireTeacher()) return;
  if (!Standard.requireActive()) return;
  Auth.populateTeacherUI();
  Standard.updateBanners();

  const std = Standard.getActive();
  const sr = await Api.getStudents(std);
  if (sr.ok) {
    students = sr.data.students || [];
    populateStudentSelect();
  }

  await loadResults();
}

function populateStudentSelect() {
  const sel = document.getElementById('resultStudentId');
  if (!sel) return;
  sel.innerHTML = '<option value="">— Select Student —</option>' +
    students.map(s => `<option value="${s._id}">Roll No: ${s.roll_no} — ${s.name}</option>`).join('');
}

async function loadResults() {
  const std = Standard.getActive();
  const tbody = document.getElementById('resultsBody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="9"><div class="loading-overlay"><div class="spinner"></div></div></td></tr>';

  const { ok, data } = await Api.getResults(std);
  if (!ok) { Toast.error(data.error || 'Failed to load results.'); return; }

  allResults = data.results || [];
  setEl3('resultCount', allResults.length);
  renderResults(allResults);
}

function renderResults(results) {
  const tbody = document.getElementById('resultsBody');
  if (!tbody) return;

  if (!results.length) {
    tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state"><div class="empty-icon">📝</div><h3>No exam results created yet</h3><p>Click "Create Complete Result" to enter all subject marks for a student.</p></div></td></tr>`;
    return;
  }

  tbody.innerHTML = results.map(r => {
    const gradeClass = 'grade-' + (r.grade || 'F').replace('+', '-plus');
    const isPass = r.status === 'Pass';

    const subPills = (r.subjects || []).map(s => `
      <span class="sub-pill">${s.subject}: <b>${s.marks}</b>/${s.max_marks}</span>
    `).join('');

    return `
    <tr>
      <td style="font-weight:700">${r.roll_no}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="student-avatar-sm">${(r.student_name || 'S')[0].toUpperCase()}</div>
          <b>${r.student_name}</b>
        </div>
      </td>
      <td><span class="badge badge-info">${r.exam_name}</span></td>
      <td>
        <div class="sub-pills-wrap">${subPills || '—'}</div>
      </td>
      <td><b>${r.total_marks}</b> / ${r.max_total}</td>
      <td><strong style="color:${r.percentage >= 70 ? '#059669' : r.percentage >= 40 ? '#D97706' : '#DC2626'}">${r.percentage}%</strong></td>
      <td><div class="grade-pill ${gradeClass}">${r.grade}</div></td>
      <td><span class="badge ${isPass ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn-outline btn-sm" title="View Full Marksheet" onclick="viewMarksheet('${r._id}')">👁️</button>
          <button class="btn btn-outline btn-sm" title="Edit Result" onclick="openEditResult('${r._id}')">✏️</button>
          <button class="btn btn-danger btn-sm" title="Delete Result" onclick="deleteResult('${r._id}')">🗑️</button>
        </div>
      </td>
    </tr>`;
  }).join('');
}

// ─── Add / Edit Modal Logic ──────────────────────────────────────────────────

function openAddResult() {
  document.getElementById('resultModal').classList.add('open');
  document.getElementById('resultForm').reset();
  document.getElementById('resultModalTitle').textContent = '➕ Create Complete Student Result';
  document.getElementById('resultId').value = '';
  document.getElementById('resultStudentId').disabled = false;
  populateStudentSelect();

  // Render default school subjects
  renderSubjectInputs(DEFAULT_SUBJECTS.map(name => ({ subject: name, marks: '', max_marks: 100 })));
  updateLiveCalculations();
}

function openEditResult(resultId) {
  const r = allResults.find(item => item._id === resultId);
  if (!r) return;

  document.getElementById('resultModal').classList.add('open');
  document.getElementById('resultModalTitle').textContent = '✏️ Edit Student Result';
  document.getElementById('resultId').value = r._id;
  
  populateStudentSelect();
  document.getElementById('resultStudentId').value = r.student_id;
  document.getElementById('resultStudentId').disabled = true;
  document.getElementById('resultExamName').value = r.exam_name;

  const subjects = r.subjects && r.subjects.length ? r.subjects : DEFAULT_SUBJECTS.map(name => ({ subject: name, marks: '', max_marks: 100 }));
  renderSubjectInputs(subjects);
  updateLiveCalculations();
}

function closeResultModal() {
  document.getElementById('resultModal').classList.remove('open');
}

function renderSubjectInputs(subjectsList) {
  const tbody = document.getElementById('subjectRowsBody');
  if (!tbody) return;

  tbody.innerHTML = subjectsList.map((s, idx) => `
    <tr class="sub-row">
      <td>
        <input type="text" class="sub-name" value="${s.subject}" placeholder="Subject name" required oninput="updateLiveCalculations()">
      </td>
      <td>
        <input type="number" class="sub-marks" value="${s.marks !== undefined ? s.marks : ''}" placeholder="0" min="0" max="1000" step="0.5" required oninput="updateLiveCalculations()">
      </td>
      <td>
        <input type="number" class="sub-max" value="${s.max_marks || 100}" placeholder="100" min="1" max="1000" required oninput="updateLiveCalculations()">
      </td>
      <td style="text-align:center">
        <button type="button" class="btn btn-danger btn-sm" style="padding:4px 8px" onclick="removeSubjectRow(this)" title="Remove Subject">❌</button>
      </td>
    </tr>
  `).join('');
}

function addCustomSubjectRow() {
  const tbody = document.getElementById('subjectRowsBody');
  if (!tbody) return;

  const tr = document.createElement('tr');
  tr.className = 'sub-row';
  tr.innerHTML = `
    <td>
      <input type="text" class="sub-name" placeholder="e.g. Computer / Sanskrit" required oninput="updateLiveCalculations()">
    </td>
    <td>
      <input type="number" class="sub-marks" placeholder="0" min="0" max="1000" step="0.5" required oninput="updateLiveCalculations()">
    </td>
    <td>
      <input type="number" class="sub-max" value="100" placeholder="100" min="1" max="1000" required oninput="updateLiveCalculations()">
    </td>
    <td style="text-align:center">
      <button type="button" class="btn btn-danger btn-sm" style="padding:4px 8px" onclick="removeSubjectRow(this)">❌</button>
    </td>
  `;
  tbody.appendChild(tr);
  updateLiveCalculations();
}

function removeSubjectRow(btn) {
  const row = btn.closest('tr');
  const tbody = document.getElementById('subjectRowsBody');
  if (tbody.querySelectorAll('.sub-row').length <= 1) {
    Toast.warning('At least one subject is required.');
    return;
  }
  row.remove();
  updateLiveCalculations();
}

function updateLiveCalculations() {
  let totalObtained = 0;
  let totalMax = 0;
  let hasFailSub = false;

  const rows = document.querySelectorAll('.sub-row');
  rows.forEach(r => {
    const marks = parseFloat(r.querySelector('.sub-marks')?.value) || 0;
    const maxM  = parseFloat(r.querySelector('.sub-max')?.value) || 100;
    totalObtained += marks;
    totalMax += maxM;

    if (maxM > 0 && (marks / maxM * 100) < 35) {
      hasFailSub = true;
    }
  });

  const pct = totalMax > 0 ? (totalObtained / totalMax * 100) : 0;
  const pctRound = Math.round(pct * 10) / 10;

  // Grade calculation
  let grade = 'F';
  if (pctRound >= 90) grade = 'A+';
  else if (pctRound >= 80) grade = 'A';
  else if (pctRound >= 70) grade = 'B+';
  else if (pctRound >= 60) grade = 'B';
  else if (pctRound >= 50) grade = 'C';
  else if (pctRound >= 40) grade = 'D';

  const status = (pctRound >= 40 && !hasFailSub) ? 'Pass' : 'Fail';

  setEl3('liveTotal', `${totalObtained} / ${totalMax}`);
  setEl3('livePct', `${pctRound}%`);
  setEl3('liveGrade', grade);
  
  const statusEl = document.getElementById('liveStatus');
  if (statusEl) {
    statusEl.textContent = status;
    statusEl.style.color = status === 'Pass' ? '#059669' : '#DC2626';
  }
}

async function submitCompleteResult(e) {
  e.preventDefault();
  const std = Standard.getActive();
  const id = document.getElementById('resultId').value;
  const studentId = document.getElementById('resultStudentId').value;
  const examName = document.getElementById('resultExamName').value.trim();

  if (!studentId && !id) {
    Toast.warning('Please select a student.');
    return;
  }

  const subjects = [];
  const rows = document.querySelectorAll('.sub-row');
  rows.forEach(r => {
    const name = r.querySelector('.sub-name')?.value.trim();
    const marks = parseFloat(r.querySelector('.sub-marks')?.value);
    const maxMarks = parseFloat(r.querySelector('.sub-max')?.value) || 100;
    if (name && !isNaN(marks)) {
      subjects.push({
        subject: name,
        marks: marks,
        max_marks: maxMarks
      });
    }
  });

  if (!subjects.length) {
    Toast.warning('Please enter marks for at least one subject.');
    return;
  }

  const payload = {
    student_id: studentId,
    standard: std,
    exam_name: examName,
    subjects: subjects
  };

  const btn = document.getElementById('saveResultBtn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Saving...'; }

  let res;
  if (id) {
    res = await Api.updateResult(id, payload);
  } else {
    res = await Api.addResult(payload);
  }

  if (btn) { btn.disabled = false; btn.textContent = '💾 Save Complete Result'; }

  if (res.ok) {
    Toast.success(id ? 'Result updated successfully!' : 'Complete result created successfully!');
    closeResultModal();
    await loadResults();
  } else {
    Toast.error(res.data.error || 'Failed to save result.');
  }
}

async function deleteResult(id) {
  if (!confirm('Are you sure you want to delete this student exam result?')) return;
  const { ok, data } = await Api.deleteResult(id);
  if (ok) {
    Toast.success('Result deleted successfully.');
    await loadResults();
  } else {
    Toast.error(data.error || 'Failed to delete result.');
  }
}

// ─── Marksheet Detail View ───────────────────────────────────────────────────

function viewMarksheet(resultId) {
  const r = allResults.find(item => item._id === resultId);
  if (!r) return;

  document.getElementById('msStudentName').textContent = `${r.student_name} (Roll No: ${r.roll_no})`;
  document.getElementById('msExamDetails').textContent = `${r.exam_name} | Standard ${r.standard}`;

  const tbody = document.getElementById('msSubjectsBody');
  if (tbody) {
    tbody.innerHTML = (r.subjects || []).map(s => {
      const pct = s.max_marks ? Math.round(s.marks / s.max_marks * 100) : 0;
      return `
        <tr>
          <td><b>${s.subject}</b></td>
          <td style="text-align:right"><b>${s.marks}</b></td>
          <td style="text-align:right">${s.max_marks}</td>
          <td style="text-align:right">${pct}%</td>
        </tr>
      `;
    }).join('');
  }

  setEl3('msTotalMarks', r.total_marks);
  setEl3('msMaxTotal', r.max_total);
  setEl3('msPercentage', `${r.percentage}%`);
  setEl3('msGrade', r.grade);

  const statusBadge = document.getElementById('msStatus');
  if (statusBadge) {
    statusBadge.textContent = r.status;
    statusBadge.className = `badge ${r.status === 'Pass' ? 'badge-success' : 'badge-danger'}`;
  }

  document.getElementById('marksheetModal').classList.add('open');
}

function closeMarksheetModal() {
  document.getElementById('marksheetModal').classList.remove('open');
}

function setEl3(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
