(function () {
  "use strict";

  const disableSubmitButtons = function (event) {
    const $submitButton = $(this).find(':submit');

    if ($submitButton.data('clicked') === 'true') {
      event.preventDefault();
      return;
    }

    $submitButton.data('clicked', 'true');

    // Add loading spinner for Send/Schedule/Cancel buttons
    const buttonName = $submitButton.attr('name')?.toLowerCase();
    if (["send", "schedule", "cancel"].includes(buttonName)) {
      // Use setTimeout with minimal delay to allow form submission to proceed first
      setTimeout(() => {
        $submitButton.prop('disabled', true);

        // Add loading spinner and aria-busy attribute for accessibility
        if ($submitButton.find('.loading-spinner').length === 0) {
          $submitButton.attr('aria-busy', 'true');
          $submitButton.append('<span class="loading-spinner" role="status" aria-label="Sending"></span>');
        }

        // Disable Cancel button too
        const $cancelButton = $('button[name]').filter(function () {
          return $(this).attr('name')?.toLowerCase() === 'cancel';
        });
        $cancelButton.prop('disabled', true);
      }, 50); // Small delay to ensure form submits first
    } else {
      setTimeout(() => renableSubmitButton($submitButton)(), 1500);
    }
  };

  const renableSubmitButton = ($submitButton) => () => {
    $submitButton.data('clicked', '');
    $submitButton.prop('disabled', false);
    $submitButton.attr('aria-busy', 'false');
    $submitButton.find('.loading-spinner').remove(); // clean up spinner
  };

  $('form').on('submit', disableSubmitButtons);
})();
