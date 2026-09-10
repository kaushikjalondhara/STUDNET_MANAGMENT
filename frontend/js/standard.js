/**
 * standard.js — Active Standard management
 * localStorage key: sms_active_standard (integer 1-12)
 *
 * USAGE ON EVERY TEACHER PAGE (except select-standard.html):
 *   Standard.requireActive();
 *   Standard.updateBanners();
 */

const Standard = {
  KEY: 'sms_active_standard',

  getActive() {
    const v = localStorage.getItem(this.KEY);
    return v ? parseInt(v) : null;
  },

  setActive(n) {
    const std = parseInt(n);
    if (std >= 1 && std <= 12) {
      localStorage.setItem(this.KEY, std);
      return std;
    }
    return null;
  },

  clear() {
    localStorage.removeItem(this.KEY);
  },

  getLabel() {
    const std = this.getActive();
    return std ? `Standard ${std}` : 'No Standard Selected';
  },

  /**
   * If no active standard → redirect to select-standard.html
   * Call this on every teacher page EXCEPT select-standard.html itself.
   */
  requireActive() {
    const std = this.getActive();
    if (!std) {
      window.location.href = '/teacher/select-standard.html';
      return false;
    }
    return true;
  },

  /**
   * Keep .std-banner sticky immediately flush beneath .top-header on all screen sizes.
   */
  updateStickyPosition() {
    const header = document.querySelector('.top-header');
    if (header) {
      if (window.innerWidth <= 768) {
        document.querySelectorAll('.std-banner').forEach(b => {
          b.style.top = '';
          b.style.position = '';
        });
        return;
      }
      const h = header.offsetHeight;
      document.querySelectorAll('.std-banner').forEach(b => {
        b.style.top = `${h}px`;
      });
    }
  },

  /**
   * Update all .std-banner-name elements in the page with the active standard label.
   * Also sets the hidden input #activeStandardInput if present and aligns sticky position.
   */
  updateBanners() {
    this.updateStickyPosition();

    const label = this.getLabel();
    const std = this.getActive();

    document.querySelectorAll('.std-banner-name').forEach(el => {
      el.textContent = label;
    });

    document.querySelectorAll('.active-std-text').forEach(el => {
      el.textContent = label;
    });

    const hiddenInput = document.getElementById('activeStandardInput');
    if (hiddenInput && std) {
      hiddenInput.value = std;
    }
  },

  /**
   * Navigate to select-standard.html (for "Change Standard" button).
   */
  changeStandard() {
    window.location.href = '/teacher/select-standard.html';
  }
};

// Ensure sticky banner position stays synced on load and screen resize
window.addEventListener('resize', () => {
  if (typeof Standard !== 'undefined' && Standard.updateStickyPosition) {
    Standard.updateStickyPosition();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  if (typeof Standard !== 'undefined' && Standard.updateStickyPosition) {
    Standard.updateStickyPosition();
  }
});
