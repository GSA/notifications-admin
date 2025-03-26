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

      // Screen reader live region
      const $srStatus = $('#upload-status-live');
      if ($srStatus.length) {
        $srStatus.text('File is uploading');
      } else {
        this.$form.prepend(`<span id="upload-status-live" class="usa-sr-only" role="status" aria-live="polite">File is uploading</span>`);
      }
    };

    this.start = function(component) {

      this.$form = $(component);

      // The label gets styled like a button and is used to hide the native file upload control. This is so that
      // users see a button that looks like the others on the site.

      this.$form.find('label.file-upload-button').addClass('usa-button margin-bottom-1').attr( {role: 'button', tabindex: '0'} );

      // Clear the form if the user navigates back to the page
      $(window).on("pageshow", () => this.$form[0].reset());

      // Need to put the event on the container, not the input for it to work properly
      this.$form.on(
        'change', '.file-upload-field',
        () => this.submit() && this.showCancelButton()
      );

    };

  };

})(window.GOVUK.Modules);
