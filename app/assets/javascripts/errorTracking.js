(function(window) {
  "use strict";

  window.NotifyModules.TrackError = function() {

    this.start = function(component) {

      // Analytics tracking removed - no longer using GOVUK analytics
      // If analytics is needed, integrate with USWDS analytics or custom solution
      console.log(
        'Error',
        $(component).data('error-type'),
        {
          'label': $(component).data('error-label')
        }
      );

    };

  };

})(window);
