(function(Modules) {
  "use strict";

  Modules.FileUpload = function() {

    this.submit = () => this.$form.trigger('submit');

    this.showCancelButton = () => $('.file-upload-button', this.$form).replaceWith(`
      <a href="" class='usa-button usa-button--secondary'>Cancel upload</a>
    `);

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
