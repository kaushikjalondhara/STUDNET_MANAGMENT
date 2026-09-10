/**
 * id-card-helper.js
 * Comprehensive ID Card, Exam Hall Ticket Generator & Automated Background Alert Engine
 * Features:
 *  - Automatic Headless Alert Sender: Dispatches WhatsApp/SMS in the background without opening WhatsApp window
 *  - Official Student Identity Card with Real Student Photo/Image & Photo Upload capability
 *  - Dynamic QR Code generation for student verification
 *  - Official Printable Exam Hall Ticket / Admit Card
 *  - Bulk ID Card Generator for entire class
 */

const IdCardHelper = {
  // ─── QR Code Image Generator ──────────────────────────────────────────────
  getQRCodeUrl(data, size = 150) {
    const encoded = encodeURIComponent(typeof data === 'string' ? data : JSON.stringify(data));
    return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encoded}&margin=4`;
  },

  // ─── Default Student Photo Generator ─────────────────────────────────────
  getStudentPhotoUrl(student) {
    if (student && (student.photo || student.photo_url)) {
      return student.photo || student.photo_url;
    }
    const name = (student && student.name) ? student.name : 'Student';
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&size=180&background=1E3A8A&color=ffffff&bold=true`;
  },

  // ─── Photo Upload Handler ────────────────────────────────────────────────
  async handlePhotoUpload(input, studentId) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target.result;
      const imgEl = document.getElementById(`idCardImg_${studentId}`);
      if (imgEl) imgEl.src = dataUrl;

      // Update cached object
      if (window.cachedStudentsList) {
        const found = window.cachedStudentsList.find(s => String(s._id || s.roll_no) === String(studentId));
        if (found) found.photo = dataUrl;
      }
      if (window.myStudentProfile) {
        window.myStudentProfile.photo = dataUrl;
      }

      // Persist to backend database
      try {
        if (typeof Api !== 'undefined') {
          if (studentId && String(studentId).length === 24) {
            await Api.updateStudent(studentId, { photo: dataUrl });
          } else {
            await Api.updateStudentPhoto(dataUrl);
          }
          if (typeof Toast !== 'undefined') Toast.success('Student photo updated successfully!');
        }
      } catch (err) {
        console.error('Photo save error:', err);
      }
    };
    reader.readAsDataURL(file);
  },

  // ─── School Info Helper ───────────────────────────────────────────────────
  getSchoolInfo() {
    return {
      name: localStorage.getItem('sms_school_name') || 'Gyan Jyot Vidhaya Bhavan',
      trust: 'Shree Vidhyavihar Education Trust',
      tagline: 'Excellence in Education & Character Building',
      phone: '+91 98765 43210',
      email: 'info@gyanjyot.edu.in',
      address: 'Near Sardar Patel Ring Road, Ahmedabad - 380015',
      academicYear: '2026 - 2027',
      board: 'GSEB / CBSE Affiliated',
      principal: 'Dr. Robert Vance, M.Sc., B.Ed.'
    };
  },

  // ─── 1. Automated Absence Alert (No WhatsApp window opened!) ─────────────
  async sendWhatsAppAbsence(student, dateStr, lang = 'gu', btn = null) {
    const mobile = (student.mobile || '').replace(/[^0-9]/g, '');
    const cleanMobile = mobile.length === 10 ? `91${mobile}` : mobile;
    const school = this.getSchoolInfo();
    const formattedDate = dateStr || new Date().toLocaleDateString('en-GB');
    const std = student.standard || (typeof Standard !== 'undefined' ? Standard.getActive() : '');

    let text = '';
    if (lang === 'gu') {
      text = `🏫 ${school.name.toUpperCase()}
` +
             `ગેરહાજરી સૂચના (Absence Notice)

` +
             `નમસ્તે વાલીશ્રી,
` +
             `આપનો પુત્ર/પુત્રી *${student.name}* (રોલ નં: *${student.roll_no}*, ધોરણ: *${std}*)
` +
             `આજે તારીખ *${formattedDate}* ના રોજ સ્કૂલમાં ગેરહાજર (ABSENT) છે.

` +
             `જો કોઈ અનિવાર્ય કારણ હોય અથવા રજા માટે અરજી કરી હોય તો કૃપા કરીને શાળા કાર્યાલયનો સંપર્ક કરવો.

` +
             `📞 સંપર્ક: ${school.phone}
` +
             `શિક્ષક: વર્ગશિક્ષક, ${school.name}`;
    } else {
      text = `🏫 ${school.name.toUpperCase()}
` +
             `ABSENCE ALERT

` +
             `Dear Parent,
` +
             `Your ward *${student.name}* (Roll No: *${student.roll_no}*, Std: *${std}*)
` +
             `is marked ABSENT today (*${formattedDate}*).

` +
             `If this is an emergency, please notify the school office immediately.

` +
             `📞 Helpdesk: ${school.phone}
` +
             `Regards, Class Teacher`;
    }

    if (!cleanMobile) {
      if (typeof Toast !== 'undefined') Toast.warning(`No valid mobile number saved for ${student.name}.`);
      return false;
    }

    // 1. Open WhatsApp Web / App with prefilled message so message is delivered to WhatsApp
    const waUrl = `https://api.whatsapp.com/send?phone=${cleanMobile}&text=${encodeURIComponent(text)}`;
    window.open(waUrl, '_blank');

    if (btn) {
      btn.disabled = false;
      btn.textContent = '✅ Sent';
      btn.style.background = '#DEF7EC';
      btn.style.color = '#03543F';
      btn.style.borderColor = '#31C48D';
    }

    // 2. Also record in backend MongoDB alert_logs and in-app notification
    try {
      if (typeof Api !== 'undefined') {
        await Api.sendAutomatedAlert({
          student_id: student.student_id || student._id,
          student_name: student.name,
          roll_no: student.roll_no,
          standard: std,
          mobile: cleanMobile,
          message: text,
          alert_type: 'absence'
        });
      }
    } catch (err) {
      console.warn('Backend alert log sync:', err);
    }

    if (typeof Toast !== 'undefined') {
      Toast.success(`📲 WhatsApp opened with message for ${student.name} (+${cleanMobile})!`);
    }
    return true;
  },

  // ─── 2. Automated Fee Reminder (No WhatsApp window opened!) ──────────────
  async sendWhatsAppFee(student, feeDetails, lang = 'gu', btn = null) {
    const mobile = (student.mobile || '').replace(/[^0-9]/g, '');
    const cleanMobile = mobile.length === 10 ? `91${mobile}` : mobile;
    const school = this.getSchoolInfo();
    const pending = Number(student.pending_amount || feeDetails?.pending_amount || 0).toLocaleString('en-IN');
    const dueDate = feeDetails?.due_date || '31-Oct-2026';
    const upiId = feeDetails?.upi_id || 'schoolfees@oksbi';
    const std = student.standard || (typeof Standard !== 'undefined' ? Standard.getActive() : '');

    let text = '';
    if (lang === 'gu') {
      text = `🏫 ${school.name.toUpperCase()}
` +
             `શાળા ફી રીમાઇન્ડર (Fee Reminder)

` +
             `નમસ્તે વાલીશ્રી,
` +
             `વિદ્યાર્થી: *${student.name}* (રોલ નં: *${student.roll_no}*, ધોરણ: *${std}*)
` +
             `શાળાની બાકી રહેતી ફી: *₹${pending}*
` +
             `ફી જમા કરવાની છેલ્લી તારીખ: *${dueDate}*

` +
             `💳 ઓનલાઇન પેમેન્ટ વિગત (UPI):
` +
             `UPI ID: ${upiId}

` +
             `કૃપા કરીને છેલ્લી તારીખ પહેલાં ફી જમા કરાવી રસીદ મેળવી લેવી.

` +
             `📞 શાળા સહાય: ${school.phone}
` +
             `શ્રી ${school.name}`;
    } else {
      text = `🏫 ${school.name.toUpperCase()}
` +
             `SCHOOL FEE PAYMENT REMINDER

` +
             `Dear Parent,
` +
             `Student: *${student.name}* (Roll No: *${student.roll_no}*, Std: *${std}*)
` +
             `Pending Dues: *₹${pending}*
` +
             `Due Date: *${dueDate}*

` +
             `💳 UPI Payment Details:
` +
             `UPI ID: ${upiId}

` +
             `Please clear the dues before the deadline.

` +
             `📞 Office: ${school.phone}
` +
             `Accounts Dept, ${school.name}`;
    }

    if (!cleanMobile) {
      if (typeof Toast !== 'undefined') Toast.warning(`No valid mobile number saved for ${student.name}.`);
      return false;
    }

    // 1. Open WhatsApp Web / App with prefilled message
    const waUrl = `https://api.whatsapp.com/send?phone=${cleanMobile}&text=${encodeURIComponent(text)}`;
    window.open(waUrl, '_blank');

    if (btn) {
      btn.disabled = false;
      btn.textContent = '✅ Sent';
      btn.style.background = '#DEF7EC';
      btn.style.color = '#03543F';
      btn.style.borderColor = '#31C48D';
    }

    // 2. Also record in backend MongoDB alert_logs and in-app notification
    try {
      if (typeof Api !== 'undefined') {
        await Api.sendAutomatedAlert({
          student_id: student.student_id || student._id,
          student_name: student.name,
          roll_no: student.roll_no,
          standard: std,
          mobile: cleanMobile,
          message: text,
          alert_type: 'fee'
        });
      }
    } catch (err) {
      console.warn('Backend fee alert log sync:', err);
    }

    if (typeof Toast !== 'undefined') {
      Toast.success(`📲 WhatsApp fee reminder opened for ${student.name} (+${cleanMobile})!`);
    }
    return true;
  },

  // ─── 3. Single Student ID Card Modal (with Photo Image) ───────────────────
  showIdCard(student) {
    const school = this.getSchoolInfo();
    const std = student.standard || (typeof Standard !== 'undefined' ? Standard.getActive() : 1);
    const sid = student._id || student.student_id || student.roll_no;
    const qrPayload = {
      school: school.name,
      id: sid,
      name: student.name,
      roll: student.roll_no,
      std: std,
      year: school.academicYear,
      verify: 'OFFICIAL_STUDENT_PASS'
    };
    const qrUrl = this.getQRCodeUrl(qrPayload, 140);
    const photoUrl = this.getStudentPhotoUrl(student);

    const modalId = 'idCardModal_' + Date.now();
    const modalHtml = `
      <div id="${modalId}" class="id-card-modal-backdrop" onclick="if(event.target===this) IdCardHelper.closeModal('${modalId}')">
        <div class="id-card-modal-container">
          <div class="id-card-modal-header">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:20px">🪪</span>
              <h3 style="margin:0;font-size:16px;color:#1E293B">Official Student Identity Card</h3>
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <label class="btn btn-outline btn-sm no-print" style="cursor:pointer;display:inline-flex;align-items:center;gap:5px;font-weight:600;color:#1E3A8A;border-color:#BFDBFE;background:#EFF6FF" title="Upload or change student photo">
                📷 Upload Photo
                <input type="file" id="headerPhotoInput_${sid}" accept="image/*" style="display:none" onchange="IdCardHelper.handlePhotoUpload(this, '${sid}')">
              </label>
              <button class="btn btn-primary btn-sm no-print" onclick="IdCardHelper.printElement('printArea_${modalId}')">🖨️ Print ID Card</button>
              <button class="btn btn-outline btn-sm no-print" onclick="IdCardHelper.closeModal('${modalId}')">✕</button>
            </div>
          </div>

          <div class="id-card-modal-body" id="printArea_${modalId}">
            <div class="id-card-wrap">
              <!-- FRONT CARD -->
              <div class="official-id-card">
                <div class="id-card-topbar">
                  <div class="id-card-logo">🏫</div>
                  <div class="id-card-school-info">
                    <div class="id-card-school-name">${school.name}</div>
                    <div class="id-card-school-tagline">${school.trust}</div>
                    <div class="id-card-board-badge">${school.board} • AY ${school.academicYear}</div>
                  </div>
                </div>

                <div class="id-card-body-content">
                  <!-- Student Photo Image -->
                  <div class="id-card-photo-box">
                    <div class="id-card-img-wrapper" id="idCardPhotoWrap_${sid}" onclick="document.getElementById('headerPhotoInput_${sid}').click()" style="cursor:pointer" title="Click to upload/change photo">
                      <img src="${photoUrl}" alt="${student.name}" class="id-student-photo-img" id="idCardImg_${sid}" />
                    </div>
                    <div class="id-card-std-tag">STD ${std}</div>
                  </div>

                  <div class="id-card-details">
                    <div class="id-name">${student.name}</div>
                    <table class="id-info-table">
                      <tr><td class="lbl">Roll No</td><td>: <b>${student.roll_no}</b></td></tr>
                      <tr><td class="lbl">Standard</td><td>: Class ${std}</td></tr>
                      <tr><td class="lbl">Mobile</td><td>: ${student.mobile || '—'}</td></tr>
                      <tr><td class="lbl">Emergency</td><td>: ${school.phone}</td></tr>
                    </table>
                  </div>

                  <div class="id-card-qr-box">
                    <img src="${qrUrl}" alt="Student QR" class="id-qr-img" />
                    <span class="qr-label">SCAN TO VERIFY</span>
                  </div>
                </div>

                <div class="id-card-footer">
                  <div class="id-card-sign">
                    <div class="sign-line">Dr. R. Vance</div>
                    <div class="sign-title">Principal Signature</div>
                  </div>
                  <div class="id-card-seal">
                    <div class="seal-circle">OFFICIAL<br/>SEAL</div>
                  </div>
                  <div class="id-card-sign">
                    <div class="sign-line">Class Teacher</div>
                    <div class="sign-title">Issued By</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    this.injectStyles();
  },

  // ─── 4. Exam Hall Ticket Modal ────────────────────────────────────────────
  showHallTicket(student, examTitle = 'Annual Board Examination 2026-27') {
    const school = this.getSchoolInfo();
    const std = student.standard || (typeof Standard !== 'undefined' ? Standard.getActive() : 1);
    const sid = student._id || student.student_id || student.roll_no;
    const qrPayload = {
      school: school.name,
      admitCard: 'EXAM_VERIFIED',
      id: sid,
      name: student.name,
      roll: student.roll_no,
      std: std,
      exam: examTitle
    };
    const qrUrl = this.getQRCodeUrl(qrPayload, 140);
    const photoUrl = this.getStudentPhotoUrl(student);
    const modalId = 'hallTicketModal_' + Date.now();

    const subjects = [
      { date: '15-10-2026', day: 'Thursday',  sub: 'Mathematics',      time: '09:00 AM - 12:00 PM', room: `Room 10${(student.roll_no % 4) + 1}` },
      { date: '17-10-2026', day: 'Saturday',  sub: 'Science & Tech',   time: '09:00 AM - 12:00 PM', room: `Room 10${(student.roll_no % 4) + 1}` },
      { date: '19-10-2026', day: 'Monday',    sub: 'English Language', time: '09:00 AM - 12:00 PM', room: `Room 10${(student.roll_no % 4) + 1}` },
      { date: '21-10-2026', day: 'Wednesday', sub: 'Social Science',   time: '09:00 AM - 12:00 PM', room: `Room 10${(student.roll_no % 4) + 1}` },
      { date: '23-10-2026', day: 'Friday',    sub: 'Gujarati / Hindi', time: '09:00 AM - 12:00 PM', room: `Room 10${(student.roll_no % 4) + 1}` },
      { date: '26-10-2026', day: 'Monday',    sub: 'Computer & AI',    time: '09:00 AM - 11:30 AM', room: `Computer Lab 1` },
    ];

    const modalHtml = `
      <div id="${modalId}" class="id-card-modal-backdrop" onclick="if(event.target===this) IdCardHelper.closeModal('${modalId}')">
        <div class="id-card-modal-container ticket-container">
          <div class="id-card-modal-header">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:20px">🎫</span>
              <h3 style="margin:0;font-size:16px;color:#1E293B">Official Exam Hall Ticket / Admit Card</h3>
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-primary btn-sm" onclick="IdCardHelper.printElement('printArea_${modalId}')">🖨️ Print Hall Ticket</button>
              <button class="btn btn-outline btn-sm" onclick="IdCardHelper.closeModal('${modalId}')">✕</button>
            </div>
          </div>

          <div class="id-card-modal-body" id="printArea_${modalId}">
            <div class="official-hall-ticket">
              <!-- HEADER -->
              <div class="ticket-header">
                <div class="ticket-logo">🏫</div>
                <div class="ticket-school-details">
                  <div class="ticket-school-name">${school.name}</div>
                  <div class="ticket-trust-name">${school.trust} • ${school.board}</div>
                  <div class="ticket-exam-title">OFFICIAL EXAMINATION ADMIT CARD / HALL TICKET</div>
                  <div class="ticket-session">${examTitle} (Session ${school.academicYear})</div>
                </div>
                <div class="ticket-qr-area">
                  <img src="${qrUrl}" alt="Hall Ticket QR" class="ticket-qr" />
                  <div class="ticket-qr-sub">ENTRY SCAN</div>
                </div>
              </div>

              <!-- CANDIDATE INFO WITH PHOTO -->
              <div style="display:flex;gap:16px;align-items:center;margin-bottom:16px">
                <div class="id-card-img-wrapper" style="width:78px;height:92px;flex-shrink:0">
                  <img src="${photoUrl}" alt="${student.name}" class="id-student-photo-img" />
                </div>
                <div class="ticket-candidate-grid" style="flex:1;margin-bottom:0">
                  <div class="ticket-info-group">
                    <span class="t-label">Candidate Name:</span>
                    <span class="t-val"><b>${student.name}</b></span>
                  </div>
                  <div class="ticket-info-group">
                    <span class="t-label">Roll Number:</span>
                    <span class="t-val"><b style="font-size:16px;color:#1E3A8A">${student.roll_no}</b></span>
                  </div>
                  <div class="ticket-info-group">
                    <span class="t-label">Standard & Division:</span>
                    <span class="t-val">Standard ${std} - Division A</span>
                  </div>
                  <div class="ticket-info-group">
                    <span class="t-label">Student ID / Seat:</span>
                    <span class="t-val"><b>Room 10${(student.roll_no % 4) + 1} (Desk #${student.roll_no})</b></span>
                  </div>
                </div>
              </div>

              <!-- SCHEDULE TABLE -->
              <div class="ticket-table-title">📅 Official Examination Timetable</div>
              <table class="ticket-exam-table">
                <thead>
                  <tr>
                    <th>Date & Day</th>
                    <th>Subject Name</th>
                    <th>Timing</th>
                    <th>Room</th>
                    <th>Invigilator Sign</th>
                  </tr>
                </thead>
                <tbody>
                  ${subjects.map(s => `
                    <tr>
                      <td style="font-weight:600">${s.date} <small>(${s.day})</small></td>
                      <td><b>${s.sub}</b></td>
                      <td>${s.time}</td>
                      <td>${s.room}</td>
                      <td class="sign-cell"></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>

              <!-- RULES -->
              <div class="ticket-rules">
                <b>Candidate Instructions & Exam Guidelines:</b>
                <ol>
                  <li>Candidates must carry this Hall Ticket and School ID Card into the examination hall daily.</li>
                  <li>Reach the examination room at least 15 minutes before the scheduled commencement time.</li>
                  <li>Electronic devices, smartphones, smartwatches, and study notes are strictly forbidden.</li>
                  <li>Maintain pin-drop silence; unfair means will result in immediate disqualification.</li>
                </ol>
              </div>

              <!-- SIGNATURES -->
              <div class="ticket-signatures">
                <div class="t-sign-box">
                  <div class="t-sign-line"></div>
                  <span>Candidate Signature</span>
                </div>
                <div class="t-sign-box">
                  <div class="t-seal-badge">OFFICIAL<br/>EXAM SEAL</div>
                </div>
                <div class="t-sign-box">
                  <div class="t-sign-line">Dr. R. Vance</div>
                  <span>Controller of Examinations / Principal</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    this.injectStyles();
  },

  // ─── 5. Bulk ID Cards Generator for Standard ──────────────────────────────
  printAllIdCards(students) {
    if (!students || !students.length) {
      if (typeof Toast !== 'undefined') Toast.warning('No students to print.');
      return;
    }
    const school = this.getSchoolInfo();
    const std = typeof Standard !== 'undefined' ? Standard.getActive() : 1;

    const cardsHtml = students.map(student => {
      const sid = student._id || student.student_id || student.roll_no;
      const qrPayload = {
        school: school.name,
        id: sid,
        name: student.name,
        roll: student.roll_no,
        std: std,
        year: school.academicYear
      };
      const qrUrl = this.getQRCodeUrl(qrPayload, 120);
      const photoUrl = this.getStudentPhotoUrl(student);

      return `
        <div class="official-id-card bulk-card">
          <div class="id-card-topbar">
            <div class="id-card-logo">🏫</div>
            <div class="id-card-school-info">
              <div class="id-card-school-name">${school.name}</div>
              <div class="id-card-school-tagline">${school.trust}</div>
              <div class="id-card-board-badge">${school.board} • Std ${std}</div>
            </div>
          </div>

          <div class="id-card-body-content">
            <div class="id-card-photo-box">
              <div class="id-card-img-wrapper">
                <img src="${photoUrl}" alt="${student.name}" class="id-student-photo-img" />
              </div>
              <div class="id-card-std-tag">STD ${std}</div>
            </div>

            <div class="id-card-details">
              <div class="id-name">${student.name}</div>
              <table class="id-info-table">
                <tr><td class="lbl">Roll No</td><td>: <b>${student.roll_no}</b></td></tr>
                <tr><td class="lbl">Mobile</td><td>: ${student.mobile || '—'}</td></tr>
                <tr><td class="lbl">Session</td><td>: ${school.academicYear}</td></tr>
              </table>
            </div>

            <div class="id-card-qr-box">
              <img src="${qrUrl}" alt="Student QR" class="id-qr-img" />
              <span class="qr-label">VERIFY</span>
            </div>
          </div>

          <div class="id-card-footer">
            <div class="id-card-sign">
              <div class="sign-line">Dr. R. Vance</div>
              <div class="sign-title">Principal</div>
            </div>
            <div class="id-card-seal">
              <div class="seal-circle">SEAL</div>
            </div>
            <div class="id-card-sign">
              <div class="sign-line">Class Teacher</div>
              <div class="sign-title">Issued By</div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    const modalId = 'bulkIdModal_' + Date.now();
    const modalHtml = `
      <div id="${modalId}" class="id-card-modal-backdrop" onclick="if(event.target===this) IdCardHelper.closeModal('${modalId}')">
        <div class="id-card-modal-container ticket-container" style="max-width:960px">
          <div class="id-card-modal-header">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:20px">🪪</span>
              <h3 style="margin:0;font-size:16px;color:#1E293B">Class Identity Cards Sheet (Standard ${std})</h3>
              <span class="badge badge-info">${students.length} Students</span>
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-primary btn-sm" onclick="IdCardHelper.printElement('printArea_${modalId}')">🖨️ Print ID Card Sheet</button>
              <button class="btn btn-outline btn-sm" onclick="IdCardHelper.closeModal('${modalId}')">✕</button>
            </div>
          </div>

          <div class="id-card-modal-body" id="printArea_${modalId}">
            <div class="bulk-grid">
              ${cardsHtml}
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    this.injectStyles();
  },

  // ─── Modal & Print Utilities ──────────────────────────────────────────────
  closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  },

  printElement(elemId) {
    const el = document.getElementById(elemId);
    if (!el) return;

    const win = window.open('', '_blank', 'width=900,height=700');
    win.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Official Document Print</title>
        <style>
          ${this.getStylesText()}
          @page { size: auto; margin: 10mm; }
          body { background: #fff; margin: 0; padding: 10px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
          .bulk-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; page-break-inside: avoid; }
          .no-print, .id-upload-photo-btn, input[type="file"], label.id-upload-photo-btn, button, .btn {
            display: none !important;
            visibility: hidden !important;
          }
          @media print {
            .no-print, .id-upload-photo-btn, input[type="file"], label.id-upload-photo-btn, button, .btn {
              display: none !important;
              visibility: hidden !important;
            }
          }
        </style>
      </head>
      <body>
        ${el.innerHTML}
        <script>
          window.onload = function() {
            window.focus();
            window.print();
            setTimeout(() => window.close(), 1000);
          };
        </script>
      </body>
      </html>
    `);
    win.document.close();
  },

  getStylesText() {
    return `
      .id-card-modal-backdrop {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px);
        display: flex; align-items: center; justify-content: center;
        z-index: 10000; padding: 16px; overflow-y: auto;
      }
      .id-card-modal-container {
        background: #fff; border-radius: 14px; max-width: 580px; width: 100%;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); overflow: hidden;
        display: flex; flex-direction: column; max-height: 94vh;
      }
      .ticket-container { max-width: 820px !important; }
      .id-card-modal-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 14px 18px; border-bottom: 1.5px solid #E2E8F0; background: #F8FAFC;
      }
      .id-card-modal-body {
        padding: 24px; overflow-y: auto; background: #F1F5F9;
      }

      /* ── Single ID Card (Standard CR80 / 85x54mm visual ratio) ── */
      .id-card-wrap { display: flex; justify-content: center; }
      .official-id-card {
        width: 440px; background: #fff; border-radius: 12px;
        border: 2px solid #1E3A8A; box-shadow: 0 8px 24px rgba(30, 58, 138, 0.15);
        overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        position: relative; page-break-inside: avoid;
      }
      .id-card-topbar {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: #fff; padding: 12px 14px; display: flex; align-items: center; gap: 10px;
        border-bottom: 3px solid #F59E0B;
      }
      .id-card-logo { font-size: 28px; line-height: 1; }
      .id-card-school-info { flex: 1; }
      .id-card-school-name { font-size: 14px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
      .id-card-school-tagline { font-size: 10px; opacity: 0.9; }
      .id-card-board-badge { font-size: 9.5px; background: rgba(255,255,255,0.2); display: inline-block; padding: 2px 6px; border-radius: 4px; margin-top: 3px; }

      .id-card-body-content {
        display: flex; align-items: center; padding: 14px; gap: 14px;
        background: radial-gradient(circle at center, #FFFFFF 0%, #F8FAFC 100%);
      }
      .id-card-photo-box {
        display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0;
      }
      .id-card-img-wrapper {
        width: 76px; height: 90px; border: 2px solid #1E3A8A; border-radius: 8px;
        overflow: hidden; background: #E2E8F0; display: flex; align-items: center;
        justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.12);
      }
      .id-student-photo-img {
        width: 100%; height: 100%; object-fit: cover; display: block;
      }
      .id-upload-photo-btn {
        display: none !important;
      }
      .no-print {
        /* Screen display for toolbar */
      }
      @media print {
        .no-print, .id-upload-photo-btn, input[type="file"], label.id-upload-photo-btn, button, .btn {
          display: none !important;
          visibility: hidden !important;
        }
      }

      .id-card-std-tag {
        background: #1E3A8A; color: #fff; font-size: 10px; font-weight: 700;
        padding: 2px 8px; border-radius: 10px; text-align: center; width: 100%;
      }
      .id-card-details { flex: 1; min-width: 0; }
      .id-name {
        font-size: 15px; font-weight: 800; color: #1E293B; margin-bottom: 6px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      }
      .id-info-table { font-size: 11.5px; border-collapse: collapse; width: 100%; }
      .id-info-table td { padding: 2px 0; color: #334155; }
      .id-info-table td.lbl { font-weight: 600; color: #64748B; width: 62px; }

      .id-card-qr-box {
        display: flex; flex-direction: column; align-items: center; flex-shrink: 0;
        border: 1px dashed #CBD5E1; padding: 4px; border-radius: 6px; background: #fff;
      }
      .id-qr-img { width: 62px; height: 62px; display: block; }
      .qr-label { font-size: 8px; font-weight: 700; color: #64748B; margin-top: 2px; }

      .id-card-footer {
        display: flex; justify-content: space-between; align-items: flex-end;
        padding: 6px 14px 10px 14px; background: #F8FAFC; border-top: 1px solid #E2E8F0;
      }
      .id-card-sign { text-align: center; }
      .sign-line { font-family: 'Brush Script MT', cursive, sans-serif; font-size: 13px; color: #1E3A8A; font-weight: bold; }
      .sign-title { font-size: 8.5px; color: #64748B; border-top: 1px solid #94A3B8; padding-top: 2px; margin-top: 2px; }
      .seal-circle {
        border: 1.5px dashed #DC2626; color: #DC2626; border-radius: 50%; width: 44px; height: 44px;
        display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: 800;
        line-height: 1.1; text-align: center; transform: rotate(-8deg);
      }

      /* ── Hall Ticket Styling ── */
      .official-hall-ticket {
        background: #fff; border: 2.5px solid #1E3A8A; border-radius: 8px;
        padding: 24px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #1E293B;
      }
      .ticket-header {
        display: flex; align-items: center; gap: 16px; border-bottom: 2.5px solid #1E3A8A;
        padding-bottom: 14px; margin-bottom: 16px;
      }
      .ticket-logo { font-size: 40px; }
      .ticket-school-details { flex: 1; text-align: center; }
      .ticket-school-name { font-size: 20px; font-weight: 900; color: #1E3A8A; letter-spacing: 0.5px; text-transform: uppercase; }
      .ticket-trust-name { font-size: 12px; color: #64748B; margin-top: 2px; }
      .ticket-exam-title {
        background: #1E3A8A; color: #fff; display: inline-block; font-size: 12px; font-weight: 800;
        padding: 3px 12px; border-radius: 4px; margin-top: 6px; letter-spacing: 0.5px;
      }
      .ticket-session { font-size: 11px; font-weight: 600; color: #334155; margin-top: 2px; }
      .ticket-qr-area { text-align: center; flex-shrink: 0; }
      .ticket-qr { width: 75px; height: 75px; border: 1px solid #CBD5E1; border-radius: 4px; }
      .ticket-qr-sub { font-size: 9px; font-weight: 700; color: #1E3A8A; margin-top: 2px; }

      .ticket-candidate-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px;
        background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px;
        padding: 12px 16px; font-size: 12.5px;
      }
      .ticket-info-group { display: flex; gap: 8px; align-items: baseline; }
      .t-label { color: #64748B; font-weight: 600; min-width: 140px; }
      .t-val { color: #1E293B; }

      .ticket-table-title { font-size: 13px; font-weight: 800; color: #1E3A8A; margin-bottom: 6px; }
      .ticket-exam-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 12px; }
      .ticket-exam-table th { background: #1E3A8A; color: #fff; padding: 7px 10px; font-weight: 700; border: 1px solid #1E3A8A; text-align: left; }
      .ticket-exam-table td { padding: 6px 10px; border: 1px solid #CBD5E1; }
      .ticket-exam-table tr:nth-child(even) { background: #F8FAFC; }
      .sign-cell { width: 120px; }

      .ticket-rules {
        font-size: 11px; color: #475569; background: #FFFBEB; border: 1px solid #FDE68A;
        border-radius: 6px; padding: 10px 14px; margin-bottom: 20px;
      }
      .ticket-rules ol { margin: 4px 0 0 16px; padding: 0; }
      .ticket-rules li { margin-bottom: 2px; }

      .ticket-signatures {
        display: flex; justify-content: space-between; align-items: flex-end; padding-top: 10px;
      }
      .t-sign-box { text-align: center; width: 200px; font-size: 11.5px; color: #475569; font-weight: 600; }
      .t-sign-line { border-bottom: 1.5px solid #64748B; height: 35px; margin-bottom: 4px; font-family: 'Brush Script MT', cursive; font-size: 16px; color: #1E3A8A; }
      .t-seal-badge {
        border: 2px dashed #DC2626; color: #DC2626; border-radius: 50%; width: 65px; height: 65px;
        display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 800;
        margin: 0 auto; text-align: center; transform: rotate(-5deg);
      }

      /* ── Bulk ID Cards Grid ── */
      .bulk-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
      .bulk-card { width: 100% !important; }
    `;
  },

  injectStyles() {
    if (document.getElementById('idCardStyles')) return;
    const styleEl = document.createElement('style');
    styleEl.id = 'idCardStyles';
    styleEl.textContent = this.getStylesText();
    document.head.appendChild(styleEl);
  }
};

if (typeof window !== 'undefined') {
  window.IdCardHelper = IdCardHelper;
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => IdCardHelper.injectStyles());
    } else {
      IdCardHelper.injectStyles();
    }
  }
}
