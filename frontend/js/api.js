/**
 * api.js — Central HTTP client for SMS API calls
 * Base URL: http://localhost:5000/api
 */

const API_BASE = (function() {
  if (typeof window !== 'undefined') {
    const loc = window.location;
    if (loc.protocol === 'file:' || (loc.port && loc.port !== '5000')) {
      return 'http://localhost:5000/api';
    }
  }
  return '/api';
})();

const Api = {
  _token() {
    return localStorage.getItem('sms_token');
  },

  _headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    const t = this._token();
    if (t) h['Authorization'] = `Bearer ${t}`;
    const mgmt = sessionStorage.getItem('sms_mgmt_token');
    if (mgmt) h['X-Management-Token'] = mgmt;
    return h;
  },

  async _request(method, path, body = null) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const opts = {
      method,
      headers: this._headers(),
      signal: controller.signal
    };
    if (body !== null) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(API_BASE + path, opts);
      clearTimeout(timeoutId);
      const data = await res.json().catch(() => ({}));
      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      clearTimeout(timeoutId);
      const isTimeout = err.name === 'AbortError';
      const errMsg = isTimeout 
        ? 'Request timed out. Backend server (port 5000) is not responding.' 
        : 'Network error. Please make sure backend server is running (python backend/run.py).';
      return { ok: false, status: 0, data: { error: errMsg } };
    }
  },

  get(path)         { return this._request('GET',    path); },
  post(path, body)  { return this._request('POST',   path, body); },
  put(path, body)   { return this._request('PUT',    path, body); },
  delete(path)      { return this._request('DELETE', path); },

  // ─── Convenience wrappers ─────────────────────────────────────────────────

  // Auth
  teacherLogin(email, password) {
    return this.post('/auth/teacher/login', { email, password });
  },
  studentLogin(mobile, password) {
    return this.post('/auth/student/login', { mobile: mobile.trim(), password });
  },

  // Teacher
  getStandards() {
    return this.get('/teacher/standards');
  },
  getDashboard(standard, date) {
    const d = date ? `&date=${encodeURIComponent(date)}` : '';
    return this.get(`/teacher/dashboard?standard=${standard}${d}`);
  },

  // Students
  getStudents(standard) {
    return this.get(`/students?standard=${standard}`);
  },
  getStudent(id) {
    return this.get(`/students/${id}`);
  },
  addStudent(data) {
    return this.post('/students', data);
  },
  updateStudent(id, data) {
    return this.put(`/students/${id}`, data);
  },
  deleteStudent(id) {
    return this.delete(`/students/${id}`);
  },
  myProfile() {
    return this.get('/students/me');
  },

  // Attendance
  getAttendance(standard, date) {
    let path = `/attendance?standard=${standard}`;
    if (date) path += `&date=${date}`;
    return this.get(path);
  },
  saveAttendance(standard, date, records) {
    return this.post('/attendance/bulk', { standard, date, records });
  },
  myAttendance() {
    return this.get('/attendance/my');
  },

  // Results
  getResults(standard) {
    return this.get(`/results?standard=${standard}`);
  },
  addResult(data) {
    return this.post('/results', data);
  },
  updateResult(id, data) {
    return this.put(`/results/${id}`, data);
  },
  deleteResult(id) {
    return this.delete(`/results/${id}`);
  },
  myResults() {
    return this.get('/results/my');
  },

  // Notices
  getNotices(standard) {
    const url = standard ? `/notices?standard=${standard}` : '/notices';
    return this.get(url);
  },
  addNotice(data) {
    return this.post('/notices', data);
  },
  deleteNotice(id) {
    return this.delete(`/notices/${id}`);
  },

  // Homework
  getHomework(standard) {
    const url = standard ? `/homework?standard=${standard}` : '/homework';
    return this.get(url);
  },
  addHomework(data) {
    return this.post('/homework', data);
  },
  deleteHomework(id) {
    return this.delete(`/homework/${id}`);
  },

  // Timetable
  getTimetable(standard) {
    const url = standard ? `/timetable?standard=${standard}` : '/timetable';
    return this.get(url);
  },
  saveTimetable(standard, schedule) {
    return this.post('/timetable', { standard, schedule });
  },

  // Leaves
  getStandardLeaves(standard) {
    return this.get(`/leaves?standard=${standard}`);
  },
  getMyLeaves() {
    return this.get('/leaves/my');
  },
  applyLeave(data) {
    return this.post('/leaves/apply', data);
  },
  updateLeaveStatus(id, status, remark) {
    return this.put(`/leaves/${id}/status`, { status, remark });
  },

  // Notifications
  getMyNotifications() {
    return this.get('/notifications/my');
  },
  getUnreadNotificationsCount() {
    return this.get('/notifications/unread-count');
  },
  markNotificationRead(id) {
    return this.put(`/notifications/read/${id}`);
  },
  markAllNotificationsRead() {
    return this.put('/notifications/read-all');
  },
  sendNotification(data) {
    return this.post('/notifications/send', data);
  },

  // Fees
  getStudentFees() {
    return this.get('/fees/student');
  },
  payFee(data) {
    return this.post('/fees/pay', data);
  },
  getFeeReceipt(transactionId) {
    return this.get(`/fees/receipt/${transactionId}`);
  },
  getStandardFees(standard) {
    return this.get(`/fees/standard?standard=${standard}`);
  },
  sendFeeReminder(data) {
    return this.post('/fees/remind', data);
  },
  getPaymentSettings() {
    return this.get('/fees/settings');
  },
  savePaymentSettings(data) {
    return this.post('/fees/settings', data);
  },

  // Reports & Analytics
  getAttendanceReport(standard) {
    return this.get(`/reports/attendance?standard=${standard}`);
  },
  getResultReport(standard) {
    return this.get(`/reports/results?standard=${standard}`);
  },
  getAnalytics(standard) {
    return this.get(`/reports/analytics?standard=${standard}`);
  },

  // Notes & Study Materials
  getNotes(standard) {
    return this.get(standard ? `/notes?standard=${standard}` : '/notes');
  },
  createNote(data) {
    return this.post('/notes', data);
  },
  deleteNote(noteId) {
    return this.delete(`/notes/${noteId}`);
  },

  // ─── School Settings & Management Auth ───────────────────────────────────
  verifyManagementPassword(password) {
    return this.post('/settings/verify-password', { password });
  },
  changeManagementPassword(oldPassword, newPassword, confirmPassword) {
    return this.post('/settings/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    });
  },
  getSchoolSettings() {
    return this.get('/settings');
  },
  updateSchoolSettings(category, data) {
    const payload = { ...data };
    const mgmt = sessionStorage.getItem('sms_mgmt_token');
    if (mgmt) payload.management_token = mgmt;
    return this.put(`/settings/${category}`, payload);
  },
  getPublicSchoolInfo() {
    return this.get('/settings/public');
  },
  getHallTicketConfig(standard) {
    return this.get(`/settings/hall-ticket/${standard}`);
  },
  updateHallTicketConfig(standard, data) {
    const payload = { ...data };
    const mgmt = sessionStorage.getItem('sms_mgmt_token');
    if (mgmt) payload.management_token = mgmt;
    return this.put(`/settings/hall-ticket/${standard}`, payload);
  },
  copyHallTicketConfig(sourceStandard) {
    const payload = { source_standard: sourceStandard };
    const mgmt = sessionStorage.getItem('sms_mgmt_token');
    if (mgmt) payload.management_token = mgmt;
    return this.post('/settings/hall-ticket/copy-all', payload);
  },

  // ─── File Download & Bulk Import Helpers ──────────────────────────────────
  async downloadFile(path, defaultFilename) {
    const t = this._token();
    const headers = {};
    if (t) headers['Authorization'] = `Bearer ${t}`;
    const mgmt = sessionStorage.getItem('sms_mgmt_token');
    if (mgmt) headers['X-Management-Token'] = mgmt;

    const res = await fetch(API_BASE + path, { headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to download file');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = defaultFilename || 'download.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadStudentTemplate() {
    return this.downloadFile('/students/template', 'student_import_template.xlsx');
  },

  exportStudents(standard) {
    const q = standard ? `?standard=${standard}` : '';
    const fn = standard ? `students_standard_${standard}.xlsx` : 'all_students_directory.xlsx';
    return this.downloadFile(`/students/export${q}`, fn);
  },

  exportFees(standard) {
    return this.downloadFile(`/fees/export?standard=${standard}`, `fees_standard_${standard}.xlsx`);
  },

  exportAttendance(standard) {
    return this.downloadFile(`/reports/attendance/export?standard=${standard}`, `attendance_standard_${standard}.xlsx`);
  },

  async importStudents(formData) {
    const t = this._token();
    const headers = {};
    if (t) headers['Authorization'] = `Bearer ${t}`;
    const res = await fetch(API_BASE + '/students/import', {
      method: 'POST',
      headers,
      body: formData
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  },

  // ─── Automated Direct Background Alerts (No WhatsApp window needed) ───────
  sendAutomatedAlert(data) {
    return this.post('/alerts/send-whatsapp', data);
  },

  sendBatchAlerts(recipients, alertType = 'absence') {
    return this.post('/alerts/send-batch', { recipients, alert_type: alertType });
  },

  getAlertLogs(standard) {
    const q = standard ? `?standard=${standard}` : '';
    return this.get(`/alerts/logs${q}`);
  },

  updateStudentPhoto(photo) {
    return this.post('/students/me/photo', { photo });
  }
};

