(function () {
  "use strict";

  const disableSubmitButtons = function (event) {
    const $submitButton = $(this).find(':submit');

    if ($submitButton.data('clicked') === 'true') {
      event.preventDefault();
      return;
    }

    $submitButton.data('clicked', 'true');

    // Add dot animation for Send/Schedule/Cancel buttons
    const buttonName = $submitButton.attr('name')?.toLowerCase();
    if (["send", "schedule", "cancel"].includes(buttonName)) {
      $submitButton.prop('disabled', true);

      // Inject dot animation span if not already present
      if ($submitButton.find('.dot-anim').length === 0) {
        $submitButton.append('<span class="dot-anim" aria-hidden="true"></span>');
      }

      // Disable Cancel button too
      const $cancelButton = $('button[name]').filter(function () {
        return $(this).attr('name')?.toLowerCase() === 'cancel';
      });
      $cancelButton.prop('disabled', true);

      setTimeout(() => {
        renableSubmitButton($submitButton);
      }, 10000); // fallback safety
    } else {
      setTimeout(renableSubmitButton($submitButton), 1500);
    }
  };

  const renableSubmitButton = ($submitButton) => () => {
    $submitButton.data('clicked', '');
    $submitButton.prop('disabled', false);
    $submitButton.find('.dot-anim').remove(); // clean up if needed
  };

  $('form').on('submit', disableSubmitButtons);
})();
