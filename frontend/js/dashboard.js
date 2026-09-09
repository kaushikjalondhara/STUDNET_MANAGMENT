/**
 * dashboard.js — Teacher / Admin Dashboard Attendance & Statistics Logic
 * 
 * Accurately calculates:
 * - Total Students (Filtered strictly by selectedStandard)
 * - Present Today (Filtered by selectedStandard + selectedDate, deduplicated)
 * - Absent Today (Filtered by selectedStandard + selectedDate, deduplicated)
 * - Not Marked (Total Students - Present Today - Absent Today)
 * - Attendance Percentage
 * - Class Average
 */

// ─── Helper Functions ─────────────────────────────────────────────────────────

/**
 * Normalizes standard strings or numbers into a uniform comparable format (e.g. 2, "Standard 2" -> 2).
 */
function normalizeStandard(val) {
  if (val === null || val === undefined) return '';
  const str = String(val).trim();
  const match = str.match(/\d+/);
  return match ? parseInt(match[0], 10) : str.toLowerCase();
}

/**
 * Returns today's date formatted as YYYY-MM-DD in local time.
 */
function getTodayIsoDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Safely parses JSON from localStorage with a fallback default.
 */
function safeGetStorage(key, fallback = []) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return parsed !== null && parsed !== undefined ? parsed : fallback;
  } catch (err) {
    console.warn(`[dashboard.js] Error parsing localStorage key "${key}":`, err);
    return fallback;
  }
}

/**
 * Helper to safely update DOM text content.
 */
function setElementText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value !== undefined && value !== null ? value : '—';
  }
}

// ─── Core Attendance & Dashboard Calculation ──────────────────────────────────

/**
 * Calculates accurate dashboard statistics from localStorage data.
 * @param {string|number} rawStandard - Currently selected standard.
 * @param {string} selectedDate - Selected date in YYYY-MM-DD format.
 * @returns {object} Calculated stats.
 */
function calculateDashboardStats(rawStandard, selectedDate) {
  if (!selectedDate) {
    selectedDate = getTodayIsoDate();
  }

  const standardNorm = normalizeStandard(rawStandard);

  // 1. Get and filter students strictly by the selected standard
  const allStudents = safeGetStorage('students', []);
  const standardStudents = Array.isArray(allStudents)
    ? allStudents.filter(s => s && normalizeStandard(s.standard || s.std) === standardNorm)
    : [];

  const totalStudents = standardStudents.length;

  if (totalStudents === 0) {
    return {
      standard: rawStandard,
      selectedDate: selectedDate,
      totalStudents: 0,
      presentToday: 0,
      absentToday: 0,
      notMarked: 0,
      attendancePct: 0,
      classAverage: 0
    };
  }

  // 2. Build quick lookup set and map of student IDs belonging ONLY to this standard
  const standardStudentIdSet = new Set();
  const studentKeyMap = new Map(); // identifier -> normalized student key

  standardStudents.forEach(s => {
    // Collect all possible unique identifier fields for this student
    const keys = [];
    if (s.id !== undefined && s.id !== null) keys.push(String(s.id));
    if (s._id !== undefined && s._id !== null) keys.push(String(s._id));
    if (s.student_id !== undefined && s.student_id !== null) keys.push(String(s.student_id));
    if (s.studentId !== undefined && s.studentId !== null) keys.push(String(s.studentId));
    if (s.roll_no !== undefined && s.roll_no !== null) keys.push(String(s.roll_no));

    // Primary unique key for the student in our counting map
    const primaryKey = keys[0] || `std_student_${Math.random()}`;
    standardStudentIdSet.add(primaryKey);

    keys.forEach(k => {
      studentKeyMap.set(k, primaryKey);
    });
  });

  // 3. Process attendance records for this date and standard
  // Map: primaryStudentKey -> 'present' | 'absent'
  const studentAttendanceMap = new Map();

  const allAttendance = safeGetStorage('attendance', []);
  if (Array.isArray(allAttendance)) {
    allAttendance.forEach(record => {
      if (!record) return;

      // Filter by selected date
      const recDate = String(record.date || '').trim();
      if (recDate !== selectedDate) return;

      // If record explicitly has a standard, make sure it matches
      if (record.standard !== undefined && record.standard !== null && String(record.standard).trim() !== '') {
        if (normalizeStandard(record.standard) !== standardNorm) {
          return; // Skip cross-standard records
        }
      }

      // Identify student from record
      const recStudentId = String(
        record.student_id ||
        record.studentId ||
        record.id ||
        record._id ||
        record.roll_no ||
        ''
      ).trim();

      if (!recStudentId || !studentKeyMap.has(recStudentId)) {
        return; // Student does not belong to this standard!
      }

      const primaryKey = studentKeyMap.get(recStudentId);
      const rawStatus = String(record.status || '').toLowerCase().trim();

      // Deduplication: 1 student gets 1 recorded status per date
      if (rawStatus === 'present' || rawStatus === 'absent') {
        studentAttendanceMap.set(primaryKey, rawStatus);
      }
    });
  }

  // 4. Count Present & Absent strictly among the enrolled standard students
  let presentCount = 0;
  let absentCount = 0;

  standardStudentIdSet.forEach(primaryKey => {
    const status = studentAttendanceMap.get(primaryKey);
    if (status === 'present') {
      presentCount++;
    } else if (status === 'absent') {
      absentCount++;
    }
  });

  // 5. Not Marked = Total Students - Present - Absent (Never negative)
  const notMarkedCount = Math.max(0, totalStudents - presentCount - absentCount);

  // 6. Attendance percentage for the day
  const attPct = totalStudents > 0 ? Math.round((presentCount / totalStudents) * 1000) / 10 : 0;

  // 7. Calculate Class Average (from results or student data)
  let classAverage = 0;
  const allResults = safeGetStorage('results', safeGetStorage('exam_results', []));
  const standardResults = Array.isArray(allResults)
    ? allResults.filter(r => r && normalizeStandard(r.standard || r.std) === standardNorm)
    : [];

  if (standardResults.length > 0) {
    const totalScores = standardResults.reduce((acc, r) => {
      const score = parseFloat(r.percentage || r.avg_score || r.marks_obtained || r.score || 0);
      return acc + (isNaN(score) ? 0 : score);
    }, 0);
    classAverage = Math.round((totalScores / standardResults.length) * 10) / 10;
  } else {
    // If students have embedded marks
    let sumMarks = 0;
    let countMarks = 0;
    standardStudents.forEach(s => {
      if (s.marks !== undefined && s.marks !== null) {
        const m = parseFloat(s.marks);
        if (!isNaN(m)) { sumMarks += m; countMarks++; }
      }
    });
    if (countMarks > 0) {
      classAverage = Math.round((sumMarks / countMarks) * 10) / 10;
    }
  }

  return {
    standard: rawStandard,
    selectedDate: selectedDate,
    totalStudents: totalStudents,
    presentToday: presentCount,
    absentToday: absentCount,
    notMarked: notMarkedCount,
    attendancePct: attPct,
    classAverage: classAverage
  };
}

// ─── UI Render & Dashboard Loader ─────────────────────────────────────────────

let currentDashboardDate = getTodayIsoDate();

/**
 * Main dashboard initialization & rendering function.
 * @param {string} [customDate] - Optional date in YYYY-MM-DD format.
 */
async function loadDashboard(customDate) {
  // 1. Get selected standard from localStorage
  const selectedStandard = 
    localStorage.getItem('selectedStandard') || 
    localStorage.getItem('activeStandard') || 
    '1';

  // 2. Determine active date
  if (customDate) {
    currentDashboardDate = customDate;
  } else {
    const dateInput = document.getElementById('dashboardDate');
    currentDashboardDate = (dateInput && dateInput.value) ? dateInput.value : getTodayIsoDate();
  }

  // Update date picker input if present in DOM
  const dateInput = document.getElementById('dashboardDate');
  if (dateInput && dateInput.value !== currentDashboardDate) {
    dateInput.value = currentDashboardDate;
  }

  // Update active standard banner
  const stdBannerName = document.getElementById('stdBannerName');
  if (stdBannerName) {
    const num = normalizeStandard(selectedStandard);
    stdBannerName.textContent = `Standard ${num}`;
  }

  // 3. Try fetching from Backend API first (if backend is active)
  let statsLoaded = false;
  if (typeof Api !== 'undefined' && typeof Api.getDashboard === 'function') {
    try {
      const stdNum = normalizeStandard(selectedStandard);
      const { ok, data } = await Api.getDashboard(stdNum, currentDashboardDate);
      if (ok && data && data.stats) {
        const s = data.stats;
        renderDashboardUI({
          totalStudents: s.total_students ?? 0,
          presentToday:  s.present_today ?? 0,
          absentToday:   s.absent_today ?? 0,
          notMarked:     s.not_marked ?? 0,
          attendancePct: s.attendance_pct ?? 0,
          classAverage:  s.class_average ?? 0
        });
        statsLoaded = true;
      }
    } catch (err) {
      console.warn('[dashboard.js] API unavailable, falling back to localStorage:', err);
    }
  }

  // 4. If API not loaded or offline, calculate from LocalStorage
  if (!statsLoaded) {
    const calculated = calculateDashboardStats(selectedStandard, currentDashboardDate);
    renderDashboardUI(calculated);
  }
}

/**
 * Renders calculated statistics into dashboard DOM elements.
 */
function renderDashboardUI(stats) {
  setElementText('totalStudents', stats.totalStudents);
  setElementText('presentToday',  stats.presentToday);
  setElementText('absentToday',   stats.absentToday);
  setElementText('notMarked',     stats.notMarked);
  setElementText('attendancePct', `${stats.attendancePct}%`);
  setElementText('classAverage',  `${stats.classAverage}%`);

  const bar = document.getElementById('attendanceBar');
  if (bar) {
    bar.style.width = `${Math.min(100, Math.max(0, stats.attendancePct))}%`;
  }
}

/**
 * Event listener for date change in dashboard date picker.
 */
/**
 * Event listener for date change in dashboard date picker.
 */
function onDashboardDateChange(newDate) {
  if (!newDate) newDate = getTodayIsoDate();
  const currentDateEl = document.getElementById('currentDate');
  if (currentDateEl) {
    try {
      const [y, m, d] = newDate.split('-').map(Number);
      const dateObj = new Date(y, m - 1, d);
      currentDateEl.textContent = dateObj.toLocaleDateString('en-IN', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
      });
    } catch (e) {
      currentDateEl.textContent = newDate;
    }
  }
  loadDashboard(newDate);
}

// ─── Auto Initialization on Page Load ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Set default date in date picker
  const dateInput = document.getElementById('dashboardDate');
  if (dateInput && !dateInput.value) {
    dateInput.value = getTodayIsoDate();
  }

  // Set formatted current date text if container exists
  const currentDateEl = document.getElementById('currentDate');
  if (currentDateEl) {
    try {
      const initialDate = (dateInput && dateInput.value) ? dateInput.value : getTodayIsoDate();
      const [y, m, d] = initialDate.split('-').map(Number);
      const dateObj = new Date(y, m - 1, d);
      currentDateEl.textContent = dateObj.toLocaleDateString('en-IN', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
      });
    } catch (e) {
      currentDateEl.textContent = new Date().toDateString();
    }
  }

  // Load dashboard
  loadDashboard();
});
