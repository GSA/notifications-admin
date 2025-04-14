// Initialize GOV.UK Frontend components (modern init)
window.GOVUKFrontend.initAll();

var showHideContent = new GOVUK.ShowHideContent();
showHideContent.init();

document.addEventListener('DOMContentLoaded', () => {
  // Autofocus the first error input
  const errorEl = document.querySelector('.error-message, .usa-error-message');
  if (errorEl) {
    const label = errorEl.closest('label');
    if (label) {
      const input = label.nextElementSibling;
      if (input && input.focus) {
        input.focus();
      }
    }
  }

  // Optional: highlight header on click
  const header = document.querySelector('.govuk-header__container');
  if (header) {
    header.addEventListener('click', () => {
      header.style.borderColor = '#005ea5';
    });
  }

  // Focus styling for heading-wrapped links
  const containers = document.querySelectorAll('.js-mark-focus-on-parent');
  containers.forEach(container => {
    container.addEventListener('focusin', e => {
      e.target.parentElement.classList.add('js-child-has-focus');
    });
    container.addEventListener('focusout', e => {
      e.target.parentElement.classList.remove('js-child-has-focus');
    });
  });
});
