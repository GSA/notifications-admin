function announceUploadStatusFromElement() {
  const srRegion = document.getElementById('upload-status-live');
  const success = document.getElementById('upload-success');
  const error = document.getElementById('upload-error');

  if (!srRegion) return;

  const message = error?.textContent || success?.textContent;

  if (message) {
    srRegion.textContent = '';
    setTimeout(() => {
      srRegion.textContent = message + '\u00A0'; // add a non-breaking space
      srRegion.focus(); // Optional
    }, 300);
  }
}


// Exported for use in tests
function initUploadStatusAnnouncer() {
  document.addEventListener('DOMContentLoaded', () => {
    announceUploadStatusFromElement();
  });
}

(function(window) {
  "use strict";

  window.NotifyModules['file-upload'] = function() {
    this.submit = () => this.form.submit();

    this.showCancelButton = () => {
      const uploadButton = this.form.querySelector('.file-upload-button');
      if (uploadButton) {
        uploadButton.outerHTML = `
          <button class='usa-button uploading-button' aria-disabled="true" tabindex="0">
            Uploading<span class="loading-spinner" role="status" aria-label="Uploading"></span>
          </button>
        `;
      }
    };

    this.start = function(component) {
      this.form = component;

      this.form.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-module="upload-trigger"]');
        if (trigger) {
          const inputId = trigger.dataset.fileInputId;
          const fileInput = document.getElementById(inputId);
          if (fileInput) fileInput.click();
        }
      });

      window.addEventListener("pageshow", () => this.form.reset());

      this.form.addEventListener('change', (event) => {
        if (event.target.closest('.file-upload-field')) {
          this.submit();
          this.showCancelButton();
        }
      });
    };
  };
})(window);

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    announceUploadStatusFromElement,
    initUploadStatusAnnouncer
  };
}

if (typeof window !== 'undefined') {
  initUploadStatusAnnouncer();
}
