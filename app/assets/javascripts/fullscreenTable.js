(function () {
  'use strict';

  function initFullscreenTables() {
    const tables = document.querySelectorAll('.fullscreen-table');

    tables.forEach((component) => {
      const table = component.querySelector('table');
      const wrapper = component.querySelector('.table-wrapper');
      const rightShadow = component.querySelector('.fullscreen-right-shadow');

      if (!table || !wrapper) return;

      const toggleShadows = () => {
        const scrollLeft = wrapper.scrollLeft;
        const maxScrollLeft = wrapper.scrollWidth - wrapper.clientWidth;

        wrapper.classList.toggle('scrolled', scrollLeft > 0);

        if (rightShadow) {
          rightShadow.classList.toggle('visible', scrollLeft < maxScrollLeft);
        }
      };

      wrapper.addEventListener('scroll', toggleShadows);
      toggleShadows(); // init state
    });
  }

  // Run once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFullscreenTables);
  } else {
    initFullscreenTables();
  }
})();
