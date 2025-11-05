(function() {
  'use strict';

  function scrollToElement(element, delay) {
    setTimeout(function() {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    }, delay || 0);
  }

  function focusFirstInput(container, delay) {
    setTimeout(function() {
      var input = container.querySelector('input[type="text"], input[type="email"]');
      if (input) input.focus();
    }, delay || 0);
  }

  function highlightAndScrollToService(serviceId) {
    var serviceRow = document.getElementById('service-' + serviceId);
    if (serviceRow) {
      scrollToElement(serviceRow, 300);

      setTimeout(function() {
        serviceRow.classList.remove('is-highlighted');
        if (serviceRow.className === '') {
          serviceRow.removeAttribute('class');
        }
      }, 3300);
    }
  }

  function initForms() {
    requestAnimationFrame(function() {
      var form = document.getElementById('create-service-form') ||
                 document.getElementById('invite-user-form') ||
                 document.getElementById('edit-service-form');

      if (form) {
        scrollToElement(form, 50);
        focusFirstInput(form, 150);
      }
    });
  }

  function initEditServiceConfirmation() {
    var confirmEditButton = document.getElementById('edit-service-confirm-btn');
    if (confirmEditButton) {
      confirmEditButton.addEventListener('click', function() {
        var editForm = document.getElementById('edit-service-form');
        if (editForm) {
          editForm.submit();
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    initForms();
    initEditServiceConfirmation();
  });

  window.OrganizationDashboard = {
    highlightAndScrollToService: highlightAndScrollToService
  };
})();
