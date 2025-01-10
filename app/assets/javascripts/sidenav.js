document.addEventListener('DOMContentLoaded', () => {
    const sidenavItems = document.querySelectorAll('.usa-sidenav__item > .parent-link');
    let lastPath = window.location.pathname;
    let debounceTimeout = null;

    sidenavItems.forEach((link) => {
      const parentItem = link.parentElement;
      const sublist = parentItem.querySelector('.usa-sidenav__sublist');
      const targetHref = link.getAttribute('href');

      // initialize the menu to open the correct submenu based on the current route
      if (window.location.pathname.startsWith(targetHref)) {
        parentItem.classList.add('open');
        link.setAttribute('aria-expanded', 'true');
      }

      link.addEventListener('click', (event) => {
        const currentPath = window.location.pathname;

        // prevent default behavior only if navigating to the same route
        if (currentPath === targetHref) {
          event.preventDefault();
          return;
        }

        if (sublist && !parentItem.classList.contains('open')) {
          // debounce the menu update to avoid flickering
          clearTimeout(debounceTimeout);
          debounceTimeout = setTimeout(() => {
            parentItem.classList.add('open');
            link.setAttribute('aria-expanded', 'true');
          }, 50);
        }
      });
    });

    // handle browser back/forward navigation
    window.addEventListener('popstate', () => {
      const currentPath = window.location.pathname;

      // sync menu state
      sidenavItems.forEach((link) => {
        const parentItem = link.parentElement;
        const targetHref = link.getAttribute('href');

        if (currentPath.startsWith(targetHref)) {
          parentItem.classList.add('open');
          link.setAttribute('aria-expanded', 'true');
        } else {
          parentItem.classList.remove('open');
          link.setAttribute('aria-expanded', 'false');
        }
      });

      lastPath = currentPath;
    });
  });
