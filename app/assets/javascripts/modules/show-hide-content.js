(function (window) {
  'use strict';

  // this javascript could be removed in the future since it is only being used
  // on the page "send-files-by-email". which is not currently in use.
  function ShowHideContent () {
    var self = this;
    var eventHandlers = new Map();

    var selectors = {
      namespace: 'ShowHideContent',
      radio: '[data-target] > input[type="radio"]',
      checkbox: '[data-target] > input[type="checkbox"]'
    };

    function initToggledContent (control) {
      var content = getToggledContent(control);

      if (content) {
        control.setAttribute('aria-controls', content.getAttribute('id'));
        control.setAttribute('aria-expanded', 'false');
        content.setAttribute('aria-hidden', 'true');
      }
    }

    function getToggledContent (control) {
      try {
        var id = control.getAttribute('aria-controls');

        if (!id) {
          var parent = control.closest('[data-target]');
          id = parent ? parent.dataset.target : null;
        }

        if (!id || !/^[\w-]+$/.test(id)) {
          console.warn('Invalid element ID:', id);
          return null;
        }

        return document.getElementById(id);
      } catch (error) {
        console.error('Error getting toggled content:', error);
        return null;
      }
    }

    function showToggledContent (control, content) {
      if (content.classList.contains('display-none')) {
        content.classList.remove('display-none');
        content.setAttribute('aria-hidden', 'false');

        if (control.getAttribute('aria-controls')) {
          control.setAttribute('aria-expanded', 'true');
        }
      }
    }

    function hideToggledContent (control, content) {
      content.classList.add('display-none');
      content.setAttribute('aria-hidden', 'true');

      if (control.getAttribute('aria-controls')) {
        control.setAttribute('aria-expanded', 'false');
      }
    }

    function handleRadioContent (control, content) {
      var selector = selectors.radio + '[name=' + escapeElementName(control.getAttribute('name')) + ']';
      var radios = document.querySelectorAll(selector);

      radios.forEach(function (radio) {
        var radioContent = getToggledContent(radio);
        if (radioContent) {
          hideToggledContent(radio, radioContent);
        }
      });

      if (content) {
        showToggledContent(control, content);
      }
    }

    function handleCheckboxContent (control, content) {
      if (!content) {
        return;
      }
      if (control.checked) {
        showToggledContent(control, content);
      } else {
        hideToggledContent(control, content);
      }
    }

    function escapeElementName (str) {
      // First escape backslashes, then escape other special characters
      // This prevents double-escaping issues identified by CodeQL
      return str ? str.replace(/\\/g, '\\\\').replace(/([!"#$%&'()*+,./:;<=>?@[\]^`{|}~])/g, '\\$1') : str;
    }

    function setupHandlers () {
      var radios = document.querySelectorAll(selectors.radio);
      var checkboxes = document.querySelectorAll(selectors.checkbox);

      radios.forEach(function (radio) {
        var handler = function () {
          handleRadioContent(radio, getToggledContent(radio));
        };
        radio.addEventListener('click', handler);
        eventHandlers.set(radio, handler);
      });

      checkboxes.forEach(function (checkbox) {
        var handler = function () {
          handleCheckboxContent(checkbox, getToggledContent(checkbox));
        };
        checkbox.addEventListener('click', handler);
        eventHandlers.set(checkbox, handler);
      });

      var allControls = Array.from(radios).concat(Array.from(checkboxes));
      var checkedControls = allControls.filter(function (control) {
        return control.checked;
      });

      if (checkedControls.length) {
        checkedControls.forEach(function (control) {
          var content = getToggledContent(control);

          if (content) {
            if (control.type === 'radio') {
              handleRadioContent(control, content);
            } else {
              handleCheckboxContent(control, content);
            }
          }
        });
      }
    }

    self.destroy = function () {
      var radios = document.querySelectorAll(selectors.radio);
      var checkboxes = document.querySelectorAll(selectors.checkbox);
      var allControls = Array.from(radios).concat(Array.from(checkboxes));

      allControls.forEach(function (control) {
        var content = getToggledContent(control);

        control.removeAttribute('aria-controls');
        control.removeAttribute('aria-expanded');
        if (content) {
          content.removeAttribute('aria-hidden');
        }

        var handler = eventHandlers.get(control);
        if (handler) {
          control.removeEventListener('click', handler);
          eventHandlers.delete(control);
        }
      });
    };

    self.init = function () {
      try {
        var radios = document.querySelectorAll(selectors.radio);
        var checkboxes = document.querySelectorAll(selectors.checkbox);
        var allControls = Array.from(radios).concat(Array.from(checkboxes));

        allControls.forEach(initToggledContent);
        setupHandlers();

      } catch (error) {
        console.error('Error initializing show-hide content:', error);
      }
    };
  }

  ShowHideContent.prototype.start = function (element) {
    try {
      var instance = new ShowHideContent();
      instance.init(element);
    } catch (error) {
      console.error('Failed to start show-hide content module:', error);
    }
  };

  window.NotifyModules.ShowHideContent = ShowHideContent;

})(window);
