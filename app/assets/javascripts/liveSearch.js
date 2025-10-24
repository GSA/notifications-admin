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

  let filter = (searchBox, searchLabel, liveRegion, targets) => () => {

    let query = normalize(searchBox.value);
    let results = 0;
    let noResultsMessage = document.querySelector('.js-live-search-no-results');

    targets.forEach(function(target) {

      let relevantElement = target.querySelector('.live-search-relevant');
      let content = relevantElement ? relevantElement.textContent : target.textContent;

      if (target.querySelector(':checked')) {
        target.classList.remove('js-hidden');
        results++;
        return;
      }

      if (query == '') {
        target.classList.remove('js-hidden');
        results++;
        return;
      }

      let isMatch = normalize(content).includes(normalize(query));

      if (isMatch) {
        target.classList.remove('js-hidden');
        results++;
      } else {
        target.classList.add('js-hidden');
      }
    });

    if (noResultsMessage) {
      if (query !== '' && results === 0) {
        noResultsMessage.classList.remove('js-hidden');
      } else {
        noResultsMessage.classList.add('js-hidden');
      }
    }

    if (state === 'loaded') {
      if (query !== '') {
        searchBox.setAttribute('aria-label', searchLabel.textContent.trim() + ', ' + resultsSummary(results));
      }
      state = 'active';
    } else {
      searchBox.removeAttribute('aria-label');
      liveRegion.textContent = resultsSummary(results);
    }

    // make sticky JS recalculate its cache of the element's position
    // because live search can change the height document
    if (window.NotifyModules && 'stickAtBottomWhenScrolling' in window.NotifyModules) {
      window.NotifyModules.stickAtBottomWhenScrolling.recalculate();
    }

  };


  Modules['live-search'] = function() {

    this.start = function(component) {

      let searchBox = component.querySelector('input');
      let searchLabel = component.querySelector('label');
      let liveRegion = component.querySelector('.live-search__status');

      let targetsSelector = component.dataset.targets;
      let targets = Array.from(document.querySelectorAll(targetsSelector));

      let filterFunc = filter(
        searchBox,
        searchLabel,
        liveRegion,
        targets
      );

      state = 'loaded';

      searchBox.addEventListener('keyup', filterFunc);
      searchBox.addEventListener('input', filterFunc);

      filterFunc();

    };

  };

})(window);
