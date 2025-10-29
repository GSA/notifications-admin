(function (window) {
  'use strict';

  window.NotifyModules.moduleSystem = {
    find: function (container) {
      container = container || document.body;

      var modules;
      var moduleSelector = '[data-module]';

      // If container is already an element, use it directly
      if (container instanceof Element) {
        modules = Array.from(container.querySelectorAll(moduleSelector));

        // If the container itself is a module, include it
        if (container.matches && container.matches(moduleSelector)) {
          modules.unshift(container);
        }
      } else {
        modules = Array.from(document.querySelectorAll(moduleSelector));
      }

      return modules;
    },

    start: function (container) {
      var modules = this.find(container);

      for (var i = 0, l = modules.length; i < l; i++) {
        try {
          var module;
          var element = modules[i];
          var type = this.camelCaseAndCapitalise(element.dataset.module);
          var started = element.dataset.moduleStarted;

          if (typeof window.NotifyModules[type] === 'function' && !started) {
            module = new window.NotifyModules[type]();
            if (module.start) {
              module.start(element);
            }
            element.dataset.moduleStarted = 'true';
          }
        } catch (error) {
          console.error('Failed to initialize module:', type || 'unknown', error);
        }
      }
    },

    camelCaseAndCapitalise: function (string) {
      return this.capitaliseFirstLetter(this.camelCase(string));
    },

    camelCase: function (string) {
      return string.replace(/-([a-z])/g, function (g) {
        return g.charAt(1).toUpperCase();
      });
    },

    capitaliseFirstLetter: function (string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    }
  };

})(window);
