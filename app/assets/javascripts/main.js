// Initialize USWDS components
if (window.uswds) {
  window.uswds.init();
}

// Initialize custom modules
window.NotifyModules.start = function() {
  var modules = document.querySelectorAll('[data-module]');
  modules.forEach(function(element) {
    var moduleName = element.getAttribute('data-module');
    var moduleStarted = element.getAttribute('data-module-started');

    if (!moduleStarted && window.NotifyModules[moduleName]) {
      var module = new window.NotifyModules[moduleName]();
      if (module.start) {
        module.start(element);
      }
      element.setAttribute('data-module-started', 'true');
    }
  });
};

document.addEventListener('DOMContentLoaded', function() {
  window.NotifyModules.start();

  const errorElement = document.querySelector('.error-message, .usa-error-message');
  if (errorElement) {
    const label = errorElement.closest('label');
    if (label && label.nextElementSibling && label.nextElementSibling.tagName === 'INPUT') {
      label.nextElementSibling.focus();
    }
  }
});
// Applies our expanded focus style to the siblings of links when that link is wrapped in a heading.
//
// This will be possible in CSS in the future, using the :has pseudo-class. When :has is available
// in the browsers we support, this code can be replaced with a CSS-only solution.
document.addEventListener('DOMContentLoaded', function() {
  const markFocusElements = document.querySelectorAll('.js-mark-focus-on-parent');
  markFocusElements.forEach(element => {
    element.addEventListener('focusin', function(e) {
      e.target.parentElement.classList.add('js-child-has-focus');
    });
    element.addEventListener('focusout', function(e) {
      e.target.parentElement.classList.remove('js-child-has-focus');
    });
  });
});
