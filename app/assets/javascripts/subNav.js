(function(window) {
    "use strict";

    document.addEventListener('DOMContentLoaded', function() {
        const sideNavLinks = document.querySelectorAll('.usa-sidenav__item');
        const currentURL = window.location.pathname;

        sideNavLinks.forEach(link => {
            const sublist = link.querySelector('.usa-sidenav__sublist');
            const parentLink = link.querySelector('a');

            const isMatch = parentLink && sublist && currentURL === parentLink.getAttribute('href');
            if (isMatch) {
                sublist.classList.replace('display-none', 'display-block');
            }

            link.addEventListener('click', function(event) {
                if (sublist && event.target === parentLink) {
                    event.preventDefault();

                    sublist.classList.toggle('display-none');
                    sublist.classList.toggle('display-block');

                    setTimeout(() => window.location.href = parentLink.href, 100);
                }
            });
        });
    });
})(window);
