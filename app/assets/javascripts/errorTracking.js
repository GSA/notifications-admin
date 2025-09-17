(function(window) {
  "use strict";

  window.NotifyModules = window.NotifyModules || {};
  window.NotifyModules['track-error'] = function() {

    this.start = function(element) {
      var component = $(element);

      // Track error to analytics if available
      if (window.NotifyModules && window.NotifyModules.analytics && window.NotifyModules.analytics.trackEvent) {
        window.NotifyModules.analytics.trackEvent(
          'Error',
          component.data('error-type'),
          {
            'label': component.data('error-label')
          }
        );
      }

    };

  };

})(window);
