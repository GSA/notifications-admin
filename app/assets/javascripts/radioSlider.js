(function(window) {

  "use strict";

  window.NotifyModules['radio-slider'] = function() {

    this.start = function(component) {

      $(component)
        .on('click', function() {

          valuesInLabel = $(this).find(':checked').next('label').text().split('/');

          if (valuesInLabel.length === 2) {
            leftValue = valuesInLabel[0];
            rightValue = valuesInLabel[1];
            $(this).find('.radio-slider-left-value').text(leftValue);
            $(this).find('.radio-slider-right-value').text(rightValue);
          }

        })
        .trigger('click');

    };

  };

})(window);
