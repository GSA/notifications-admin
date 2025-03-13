(function() {

  "use strict";

  let disableSubmitButtons = function(event) {

    var $submitButton = $(this).find(':submit');

    if ($submitButton.data('clicked') == 'true') {

      event.preventDefault();

    } else {

      $submitButton.data('clicked', 'true');
      $submitButton.prop('disabled', true);
      setTimeout(renableSubmitButton($submitButton), 10000);

    }

  };

  let renableSubmitButton = $submitButton => () => {

    $submitButton.data('clicked', '');
    $submitButton.prop('disabled', false);
  };

  $('form').on('submit', disableSubmitButtons);

})();
