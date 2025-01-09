document.addEventListener('DOMContentLoaded', () => {
    const sidenavItems = document.querySelectorAll('.usa-sidenav__item > .parent-link');

    sidenavItems.forEach((link) => {
      const parentItem = link.parentElement;
      const hasChildren = parentItem.querySelector('.usa-sidenav__sublist');
      const currentUrl = window.location.pathname;

      if (
        link.getAttribute('href') === currentUrl ||
        currentUrl.startsWith(link.getAttribute('href'))
      ) {
        parentItem.classList.add('open');
        link.setAttribute('aria-expanded', 'true');
      }

      link.addEventListener('click', (event) => {
        if (hasChildren) {
          event.preventDefault();

          const isOpen = parentItem.classList.contains('open');

          document.querySelectorAll('.usa-sidenav__item.open').forEach((item) => {
            if (item !== parentItem) {
              item.classList.remove('open');
              item.querySelector('.parent-link').setAttribute('aria-expanded', 'false');
            }
          });

          if (!isOpen) {
            parentItem.classList.add('open');
            link.setAttribute('aria-expanded', 'true');
          } else {
            parentItem.classList.remove('open');
            link.setAttribute('aria-expanded', 'false');
          }

          window.location.href = link.getAttribute('href');
        }
      });
    });
  });
