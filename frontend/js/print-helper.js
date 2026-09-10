/**
 * PrintHelper — Isolated, clean printing for School Reports & Fee Receipts
 * Bypasses web page DOM and prints ONLY the clean document without sidebars,
 * headers, dark backdrops, or navigation elements.
 */
const PrintHelper = {
  /**
   * Helper to print HTML content in an isolated hidden iframe
   */
  printHtml(contentHtml, documentTitle = 'School Document') {
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');
    if (isMobile) {
      const win = window.open('', '_blank');
      if (win) {
        win.document.open();
        win.document.write(`
          <!DOCTYPE html>
          <html lang="en">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${documentTitle}</title>
            <style>
              @page { size: A4 portrait; margin: 10mm; }
              * { box-sizing: border-box; margin: 0; padding: 0; }
              body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #0f172a; background: #f8fafc; padding: 12px; font-size: 12.5px;
              }
              .receipt-frame {
                background: #fff; border: 2px solid #1e293b; border-radius: 8px;
                padding: 16px; margin: 0 auto; max-width: 650px; position: relative;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
              }
              .receipt-watermark-paid {
                position: absolute; top: 45%; left: 50%; transform: translate(-50%, -50%) rotate(-25deg);
                font-size: 54px; font-weight: 900; color: rgba(16, 185, 129, 0.12); pointer-events: none;
              }
              .official-letterhead { text-align: center; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 12px; }
              .school-emblem { font-size: 28px; margin-bottom: 2px; }
              .school-name { font-size: 18px; font-weight: 900; color: #0f172a; text-transform: uppercase; }
              .school-tagline { font-size: 11px; color: #475569; }
              .school-meta-line { font-size: 10px; color: #64748b; }
              .doc-badge-title {
                display: inline-block; background: #0f172a; color: #fff; font-size: 12px;
                font-weight: 800; padding: 3px 14px; border-radius: 4px; margin-top: 6px;
              }
              .report-meta-grid {
                display: flex; flex-direction: column; gap: 6px; background: #f8fafc;
                border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; margin-bottom: 12px; font-size: 11.5px;
              }
              .report-meta-grid div { line-height: 1.5; }
              table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 11px; }
              th { background: #0f172a; color: #fff; padding: 6px 8px; text-align: left; }
              td { border: 1px solid #cbd5e1; padding: 6px 8px; }
              .doc-footer-signatures { display: flex; flex-direction: column; align-items: center; gap: 14px; margin-top: 18px; }
              .sig-column { width: 100%; text-align: center; font-size: 10.5px; }
              .sig-line { border-top: 1.5px solid #475569; padding-top: 4px; }
              .official-stamp-box {
                border: 2px dashed #059669; color: #059669; border-radius: 6px; padding: 6px 12px; text-align: center;
              }
              .mobile-action-bar {
                display: flex; justify-content: space-between; align-items: center;
                background: #0f172a; color: #fff; padding: 10px 14px; border-radius: 8px;
                margin-bottom: 12px; position: sticky; top: 0; z-index: 100;
              }
              .mobile-action-btn {
                background: #10b981; color: #fff; border: none; padding: 8px 14px;
                border-radius: 6px; font-weight: 700; font-size: 13px; cursor: pointer;
              }
              @media print {
                .mobile-action-bar { display: none !important; }
                body { padding: 0 !important; background: #fff !important; }
                .receipt-frame { box-shadow: none !important; border: 2px solid #000 !important; }
              }
            </style>
          </head>
          <body>
            <div class="mobile-action-bar">
              <span style="font-weight:700">📄 Fee Receipt</span>
              <button class="mobile-action-btn" onclick="window.print()">📥 Download / Print PDF</button>
            </div>
            ${contentHtml}
            <script>
              setTimeout(() => { window.print(); }, 400);
            <\/script>
          </body>
          </html>
        `);
        win.document.close();
        return;
      }
    }

    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>${documentTitle}</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 12mm 15mm;
          }
          * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #0f172a;
            background: #ffffff !important;
            padding: 10px;
            font-size: 13px;
            line-height: 1.5;
          }
          .official-letterhead {
            text-align: center;
            border-bottom: 2.5px solid #1e293b;
            padding-bottom: 12px;
            margin-bottom: 16px;
            position: relative;
          }
          .school-emblem {
            font-size: 32px;
            margin-bottom: 4px;
          }
          .school-name {
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 0.5px;
            color: #0f172a;
            text-transform: uppercase;
          }
          .school-tagline {
            font-size: 12px;
            color: #475569;
            margin-top: 2px;
          }
          .school-meta-line {
            font-size: 11px;
            color: #64748b;
            margin-top: 3px;
          }
          .doc-badge-title {
            display: inline-block;
            background: #0f172a;
            color: #ffffff;
            font-size: 13px;
            font-weight: 800;
            padding: 4px 18px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-top: 10px;
          }
          .report-meta-grid {
            display: flex;
            justify-content: space-between;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 16px;
            font-size: 12px;
          }
          .report-meta-grid div {
            line-height: 1.6;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
            font-size: 12px;
          }
          th {
            background-color: #f1f5f9 !important;
            color: #0f172a;
            font-weight: 800;
            border: 1px solid #94a3b8;
            padding: 8px 10px;
            text-align: left;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.4px;
          }
          td {
            border: 1px solid #cbd5e1;
            padding: 7px 10px;
            color: #1e293b;
          }
          tr:nth-child(even) td {
            background-color: #f8fafc !important;
          }
          .text-right { text-align: right; }
          .text-center { text-align: center; }
          .font-bold { font-weight: 700; }
          .badge-pill {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid #cbd5e1;
          }
          .badge-present { background: #dcfce7 !important; color: #15803d; border-color: #86efac; }
          .badge-absent { background: #fee2e2 !important; color: #b91c1c; border-color: #fca5a5; }
          .doc-footer-signatures {
            margin-top: 36px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding: 10px 20px 0;
            page-break-inside: avoid;
          }
          .sig-column {
            text-align: center;
            width: 170px;
          }
          .sig-line {
            border-top: 1.5px solid #475569;
            margin-top: 45px;
            padding-top: 5px;
            font-size: 11px;
            font-weight: 700;
            color: #1e293b;
          }
          .official-stamp-box {
            text-align: center;
            border: 2px dashed #059669;
            color: #059669;
            border-radius: 8px;
            padding: 8px 16px;
            display: inline-block;
            transform: rotate(-3deg);
          }
          .stamp-title {
            font-size: 14px;
            font-weight: 900;
            letter-spacing: 1px;
          }
          .stamp-sub {
            font-size: 9px;
            font-weight: 700;
          }
          /* Receipt specific */
          .receipt-frame {
            border: 2px solid #1e293b;
            border-radius: 8px;
            padding: 20px 24px;
            max-width: 680px;
            margin: 0 auto;
            position: relative;
            background: #ffffff;
          }
          .receipt-watermark-paid {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-30deg);
            font-size: 80px;
            font-weight: 900;
            color: rgba(5, 150, 105, 0.08);
            pointer-events: none;
            letter-spacing: 6px;
            text-transform: uppercase;
          }
        </style>
      </head>
      <body>
        ${contentHtml}
      </body>
      </html>
    `);
    doc.close();

    iframe.contentWindow.focus();
    setTimeout(() => {
      iframe.contentWindow.print();
      setTimeout(() => {
        if (document.body.contains(iframe)) {
          document.body.removeChild(iframe);
        }
      }, 1000);
    }, 300);
  },

  /**
   * Print Official Fee Receipt Slip
   */
  printReceipt(t) {
    const studentName = t.student_name || 'Student';
    const rollNo = t.roll_no || '—';
    const std = t.standard ? `Standard ${t.standard}` : 'Standard —';
    const amount = Number(t.amount || 0);
    const receiptNo = t.receipt_no || 'REC-2026';
    const txnId = t.transaction_id || 'TXN0000';
    const utr = t.utr_number || '—';
    const date = t.date || new Date().toLocaleString();
    const mode = t.payment_mode || 'Online UPI';
    const schoolName = (typeof SchoolBranding !== 'undefined' && SchoolBranding.getName) ? SchoolBranding.getName() : (localStorage.getItem('sms_school_name') || 'Parth classic');

    const html = `
      <div class="receipt-frame">
        <div class="receipt-watermark-paid">PAID</div>
        
        <div class="official-letterhead">
          <div class="school-emblem">🏫</div>
          <div class="school-name">${schoolName}</div>
          <div class="school-tagline">Excellence in Education & Character Building</div>
          <div class="school-meta-line">Affiliated with State & Central Board | Academic Year: 2026-2027</div>
          <div class="doc-badge-title">OFFICIAL FEE PAYMENT RECEIPT</div>
        </div>

        <div class="report-meta-grid">
          <div>
            <div><b>Receipt No:</b> <span style="color:#0f172a;font-weight:800">${receiptNo}</span></div>
            <div><b>Transaction ID:</b> <span>${txnId}</span></div>
            <div><b>Bank UTR / Ref No:</b> <span style="color:#059669;font-weight:700">${utr}</span></div>
            <div><b>Payment Date:</b> <span>${date}</span></div>
          </div>
          <div style="text-align:right">
            <div><b>Student Name:</b> <span style="color:#0f172a;font-weight:800">${studentName}</span></div>
            <div><b>Roll Number:</b> <span>${rollNo}</span></div>
            <div><b>Class / Standard:</b> <span>${std}</span></div>
            <div><b>Payment Method:</b> <span style="color:#059669;font-weight:700">${mode}</span></div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th style="width:40px">Sr</th>
              <th>Fee Particulars / Description</th>
              <th style="text-align:center;width:120px">Payment Mode</th>
              <th style="text-align:right;width:140px">Amount Paid (₹)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="text-align:center">1</td>
              <td>
                <b>School Academic Term & Tuition Fee</b><br>
                <span style="font-size:11px;color:#64748b">Includes Academic Curriculum, Digital Resources, Activity & Lab Fees</span>
              </td>
              <td style="text-align:center"><b>${mode}</b></td>
              <td style="text-align:right;font-size:14px;font-weight:800;color:#0f172a">₹${amount.toLocaleString('en-IN')}.00</td>
            </tr>
          </tbody>
          <tfoot>
            <tr style="background:#f1f5f9;font-weight:800">
              <td colspan="3" style="text-align:right;font-size:13px">NET AMOUNT RECEIVED:</td>
              <td style="text-align:right;font-size:15px;color:#059669">₹${amount.toLocaleString('en-IN')}.00</td>
            </tr>
          </tfoot>
        </table>

        <div style="margin-top:10px;font-size:11px;color:#475569;border-left:3px solid #059669;padding-left:10px">
          <b>Note:</b> This is an official digital payment receipt generated by ${schoolName}. All fees paid are subject to school accounts audit.
        </div>

        <div class="doc-footer-signatures">
          <div class="sig-column">
            <div class="sig-line">STUDENT / PARENT SIGN</div>
          </div>
          
          <div class="official-stamp-box">
            <div class="stamp-title">✅ RECEIVED & VERIFIED</div>
            <div class="stamp-sub">SCHOOL ACCOUNTS OFFICE</div>
          </div>

          <div class="sig-column">
            <div class="sig-line">AUTHORIZED SIGNATORY / CASHIER</div>
          </div>
        </div>
      </div>
    `;

    this.printHtml(html, `Fee_Receipt_${receiptNo}`);
  },

  /**
   * Print Official Class Reports (Attendance, Results, Students)
   */
  printReport({ title, subtitle, standard, tableHeaders, tableRowsHtml, summaryStatsHtml = '' }) {
    const stdText = standard ? (standard.toString().includes('Standard') ? standard : `Standard ${standard}`) : 'All Classes';
    const now = new Date().toLocaleString();
    const schoolName = (typeof SchoolBranding !== 'undefined' && SchoolBranding.getName) ? SchoolBranding.getName() : (localStorage.getItem('sms_school_name') || 'Parth classic');

    const html = `
      <div>
        <div class="official-letterhead">
          <div class="school-emblem">🏫</div>
          <div class="school-name">${schoolName}</div>
          <div class="school-tagline">Comprehensive Academic Management & Evaluation System</div>
          <div class="school-meta-line">Academic Year 2026-2027</div>
          <div class="doc-badge-title">${title || 'OFFICIAL REPORT'}</div>
        </div>

        <div class="report-meta-grid">
          <div>
            <div><b>Class / Standard:</b> <span style="font-weight:800;color:#0f172a">${stdText}</span></div>
            <div><b>Report Subject:</b> <span>${subtitle || 'General Academic Report'}</span></div>
          </div>
          <div style="text-align:right">
            <div><b>Generated On:</b> <span>${now}</span></div>
            <div><b>Verified By:</b> <span>Class Teacher & Administration</span></div>
          </div>
        </div>

        ${summaryStatsHtml ? `<div style="margin-bottom:14px">${summaryStatsHtml}</div>` : ''}

        <table>
          <thead>
            <tr>
              ${tableHeaders.map(h => `<th style="${h.style || ''}">${h.label}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
            ${tableRowsHtml}
          </tbody>
        </table>

        <div class="doc-footer-signatures">
          <div class="sig-column">
            <div class="sig-line">CLASS TEACHER</div>
          </div>
          
          <div class="official-stamp-box">
            <div class="stamp-title">🏛️ OFFICIAL SCHOOL SEAL</div>
            <div class="stamp-sub">CONFIDENTIAL & CERTIFIED</div>
          </div>

          <div class="sig-column">
            <div class="sig-line">PRINCIPAL / HEAD OF SCHOOL</div>
          </div>
        </div>
      </div>
    `;

    this.printHtml(html, `${title}_${stdText}`.replace(/\s+/g, '_'));
  }
};
