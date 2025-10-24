(function(window) {
  "use strict";

  window.NotifyModules['track-error'] = function() {

    this.start = function(element) {
      // Track error to analytics if available
      if (window.NotifyModules && window.NotifyModules.analytics && window.NotifyModules.analytics.trackEvent) {
        window.NotifyModules.analytics.trackEvent(
          'Error',
          element.dataset.errorType,
          {
            'label': element.dataset.errorLabel
          }
        );
      }

    };

  };

})(window);
