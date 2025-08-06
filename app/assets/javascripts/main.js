// Initialize USWDS components
if (window.uswds) {
  window.uswds.init();
}

// Initialize custom modules
window.NotifyModules = window.NotifyModules || {};
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

$(() => window.NotifyModules.start());

$(() => $('.error-message, .usa-error-message').eq(0).parent('label').next('input').trigger('focus'));


// Applies our expanded focus style to the siblings of links when that link is wrapped in a heading.
//
// This will be possible in CSS in the future, using the :has pseudo-class. When :has is available
// in the browsers we support, this code can be replaced with a CSS-only solution.
$('.js-mark-focus-on-parent').on('focus blur', '*', e => {
  $target = $(e.target);
  if (e.type === 'focusin') {
    $target.parent().addClass('js-child-has-focus');
  } else {
    $target.parent().removeClass('js-child-has-focus');
  }
});
