(function () {
  "use strict";

  const disableSubmitButtons = function (event) {
    const form = event.currentTarget;
    const submitButton = form.querySelector('input[type="submit"], button[type="submit"]');

    if (!submitButton) return;

    if (submitButton.dataset.clicked === 'true') {
      event.preventDefault();
      return;
    }

    submitButton.dataset.clicked = 'true';

    // Add loading spinner for Send/Schedule/Cancel buttons
    const buttonName = submitButton.getAttribute('name')?.toLowerCase();
    if (["send", "schedule", "cancel"].includes(buttonName)) {
      // Use setTimeout with minimal delay to allow form submission to proceed first
      setTimeout(() => {
        submitButton.disabled = true;

        // Add loading spinner and aria-busy attribute for accessibility
        if (submitButton.querySelector('.loading-spinner') === null) {
          submitButton.setAttribute('aria-busy', 'true');
          submitButton.insertAdjacentHTML('beforeend', '<span class="loading-spinner" role="status" aria-label="Sending"></span>');
        }

        // Disable Cancel button too
        const cancelButtons = Array.from(document.querySelectorAll('button[name]')).filter(button => {
          return button.getAttribute('name')?.toLowerCase() === 'cancel';
        });
        cancelButtons.forEach(button => button.disabled = true);
      }, 50); // Small delay to ensure form submits first
    } else {
      setTimeout(() => renableSubmitButton(submitButton)(), 1500);
    }
  };

  const renableSubmitButton = (submitButton) => () => {
    submitButton.dataset.clicked = '';
    submitButton.disabled = false;
    submitButton.setAttribute('aria-busy', 'false');
    const spinner = submitButton.querySelector('.loading-spinner');
    if (spinner) spinner.remove(); // clean up spinner
  };

  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', disableSubmitButtons);
  });
})();
