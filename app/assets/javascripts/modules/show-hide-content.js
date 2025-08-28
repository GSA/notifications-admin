(function (global) {
  'use strict';

  var $ = global.jQuery;

  function ShowHideContent () {
    var self = this;

    var selectors = {
      namespace: 'ShowHideContent',
      radio: '[data-target] > input[type="radio"]',
      checkbox: '[data-target] > input[type="checkbox"]'
    };

    function initToggledContent () {
      var $control = $(this);
      var $content = getToggledContent($control);

      if ($content.length) {
        $control.attr('aria-controls', $content.attr('id'));
        $control.attr('aria-expanded', 'false');
        $content.attr('aria-hidden', 'true');
      }
    }

    function getToggledContent ($control) {
      try {
        var id = $control.attr('aria-controls');

        if (!id) {
          id = $control.closest('[data-target]').data('target');
        }

        if (!id || !/^[\w-]+$/.test(id)) {
          console.warn('Invalid element ID:', id);
          return $();
        }

        return $('#' + id);
      } catch (error) {
        console.error('Error getting toggled content:', error);
        return $();
      }
    }

    function showToggledContent ($control, $content) {
      if ($content.hasClass('display-none')) {
        $content.removeClass('display-none');
        $content.attr('aria-hidden', 'false');

        if ($control.attr('aria-controls')) {
          $control.attr('aria-expanded', 'true');
        }
      }
    }

    function hideToggledContent ($control, $content) {
      $content.addClass('display-none');
      $content.attr('aria-hidden', 'true');

      if ($control.attr('aria-controls')) {
        $control.attr('aria-expanded', 'false');
      }
    }

    function handleRadioContent ($control, $content) {
      var selector = selectors.radio + '[name=' + escapeElementName($control.attr('name')) + ']';
      var $radios = $(selector);

      $radios.each(function () {
        hideToggledContent($(this), getToggledContent($(this)));
      });

      showToggledContent($control, $content);
    }

    function handleCheckboxContent ($control, $content) {
      if ($control.is(':checked')) {
        showToggledContent($control, $content);
      } else {
        hideToggledContent($control, $content);
      }
    }

    function escapeElementName (str) {
      return str ? str.replace(/([!"#$%&'()*+,./:;<=>?@[\]^`{|}~])/g, '\\$1') : str;
    }

    function setupHandlers () {
      var $controls = $(selectors.radio + ', ' + selectors.checkbox);

      $(selectors.radio).on('click.' + selectors.namespace, function () {
        handleRadioContent($(this), getToggledContent($(this)));
      });

      $(selectors.checkbox).on('click.' + selectors.namespace, function () {
        handleCheckboxContent($(this), getToggledContent($(this)));
      });
      if ($controls.filter(':checked').length) {
        $controls.filter(':checked').each(function () {
          var $control = $(this);
          var $content = getToggledContent($control);

          if ($control.is('[type=radio]')) {
            handleRadioContent($control, $content);
          } else {
            handleCheckboxContent($control, $content);
          }
        });
      }
    }

    self.destroy = function () {
      var $controls = $(selectors.radio + ', ' + selectors.checkbox);

      $controls.each(function () {
        var $control = $(this);
        var $content = getToggledContent($control);

        $control.removeAttr('aria-controls aria-expanded');
        $content.removeAttr('aria-hidden');
      });

      $(selectors.radio).off('.' + selectors.namespace);
      $(selectors.checkbox).off('.' + selectors.namespace);
    };

    self.init = function () {
      try {
        $(selectors.radio + ', ' + selectors.checkbox).each(initToggledContent);
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

  global.NotifyModules = global.NotifyModules || {};
  global.NotifyModules.ShowHideContent = ShowHideContent;

})(window);
