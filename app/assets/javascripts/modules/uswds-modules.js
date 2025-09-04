(function (global) {
  'use strict';

  var $ = global.jQuery;

  global.NotifyModules = global.NotifyModules || {};

  global.NotifyModules.moduleSystem = {
    find: function (container) {
      container = container || $('body');

      var modules;
      var moduleSelector = '[data-module]';

      modules = container.find(moduleSelector);

      if (container.is(moduleSelector)) {
        modules = modules.add(container);
      }

      return modules;
    },

    start: function (container) {
      var modules = this.find(container);

      for (var i = 0, l = modules.length; i < l; i++) {
        try {
          var module;
          var element = $(modules[i]);
          var type = this.camelCaseAndCapitalise(element.data('module'));
          var started = element.data('module-started');

          if (typeof global.NotifyModules[type] === 'function' && !started) {
            module = new global.NotifyModules[type]();
            if (module.start) {
              module.start(element);
            }
            element.data('module-started', true);
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
