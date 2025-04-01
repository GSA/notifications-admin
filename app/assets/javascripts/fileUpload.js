function announceUploadStatusFromElement() {
  const srRegion = document.getElementById('upload-status-live');
  const success = document.getElementById('upload-success');
  const error = document.getElementById('upload-error');

  if (!srRegion) return;

  const message = error?.textContent || success?.textContent;

  if (message) {
    srRegion.textContent = '';
    setTimeout(() => {
      srRegion.textContent = message;
    }, 50);
  }
}

// Exported for use in tests
function initUploadStatusAnnouncer() {
  document.addEventListener('DOMContentLoaded', () => {
    announceUploadStatusFromElement();
  });
}

(function(Modules) {
  "use strict";

  Modules.FileUpload = function() {
    this.submit = () => this.$form.trigger('submit');

    this.showCancelButton = () => {
      $('.file-upload-button', this.$form).replaceWith(`
        <button class='usa-button uploading-button' aria-disabled="true" tabindex="0">
          Uploading<span class="dot-anim" aria-hidden="true"></span>
        </button>
      `);
    };

    this.start = function(component) {
      this.$form = $(component);

      this.$form.on('click', '[data-module="upload-trigger"]', function () {
        const inputId = $(this).data('file-input-id');
        const fileInput = document.getElementById(inputId);
        if (fileInput) fileInput.click();
      });

      $(window).on("pageshow", () => this.$form[0].reset());

      this.$form.on('change', '.file-upload-field', () => {
        this.submit();
        this.showCancelButton();
      });
    };
  };
})(window.GOVUK.Modules);

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    announceUploadStatusFromElement,
    initUploadStatusAnnouncer
  };
}
