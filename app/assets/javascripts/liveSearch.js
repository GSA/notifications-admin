(function(window) {
  "use strict";

  var Modules = window.NotifyModules;
  let state;
  let normalize = (string) => string.toLowerCase().replace(/ /g,'');
  let resultsSummary = (num) => {
    if (num === 0) {
      return "no results";
    } else {
      return num + (num === 1 ? " result" : " results");
    }
  };

  let filter = ($searchBox, $searchLabel, $liveRegion, $targets) => () => {

    let query = normalize($searchBox.val());
    let results = 0;
    let $noResultsMessage = $('.js-live-search-no-results');

    $targets.each(function() {

      let content = $('.live-search-relevant', this).text() || $(this).text();

      if ($(this).has(':checked').length) {
        $(this).show();
        results++;
        return;
      }

      if (query == '') {
        $(this).removeClass('js-hidden');
        results++;
        return;
      }

      let isMatch = normalize(content).includes(normalize(query));

      if (isMatch) {
        $(this).removeClass('js-hidden');
        results++;
      } else {
        $(this).addClass('js-hidden');
      }
    });

    if (query !== '' && results === 0) {
      $noResultsMessage.removeClass('js-hidden');
    } else {
      $noResultsMessage.addClass('js-hidden');
    }

    if (state === 'loaded') {
      if (query !== '') {
        $searchBox.attr('aria-label', $searchLabel.text().trim() + ', ' + resultsSummary(results));
      }
      state = 'active';
    } else {
      $searchBox.removeAttr('aria-label');
      $liveRegion.text(resultsSummary(results));
    }

    // make sticky JS recalculate its cache of the element's position
    // because live search can change the height document
    if (window.NotifyModules && 'stickAtBottomWhenScrolling' in window.NotifyModules) {
      window.NotifyModules.stickAtBottomWhenScrolling.recalculate();
    }

  };


  Modules['live-search'] = function() {

    this.start = function(component) {

      let $component = $(component);

      let $searchBox = $('input', $component);
      let $searchLabel = $('label', $component);
      let $liveRegion = $('.live-search__status', $component);

      let filterFunc = filter(
        $searchBox,
        $searchLabel,
        $liveRegion,
        $($component.data('targets'))
      );

      state = 'loaded';

      $searchBox.on('keyup input', filterFunc);

      filterFunc();

    };

  };

})(window);
