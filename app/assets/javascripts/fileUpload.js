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

      const $srStatus = $('#upload-status-live');
      if ($srStatus.length) {
        // Clear and re-set the content to ensure it's treated as a change
        $srStatus.html('');
        setTimeout(() => {
          $srStatus.html('<span>File is uploading</span>');
        }, 50);
      }
    };

    this.start = function(component) {

      this.$form = $(component);

      // Handle "Upload your file" button click — CSP-safe version
      this.$form.on('click', '[data-module="upload-trigger"]', function () {
        const inputId = $(this).data('file-input-id');
        const fileInput = document.getElementById(inputId);
        if (fileInput) fileInput.click();
      });

      // Clear the form if the user navigates back to the page
      $(window).on("pageshow", () => this.$form[0].reset());

      // Watch for file input changes
      this.$form.on('change', '.file-upload-field', () => {
        this.submit();
        this.showCancelButton();
      });

    };

  };

})(window.GOVUK.Modules);
