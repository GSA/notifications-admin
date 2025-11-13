(function(window) {
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

  function initDeleteServiceConfirmation() {
    var deleteButtons = document.querySelectorAll('[data-open-modal="confirmDeleteModal"]');
    var confirmDeleteButton = document.getElementById('delete-service-confirm-btn');
    var deleteServiceNameDisplay = document.getElementById('delete-service-name-display');
    var deleteForm = document.getElementById('delete-service-form');

    if (deleteButtons.length > 0 && confirmDeleteButton && deleteForm) {
      var currentServiceId = null;

      deleteButtons.forEach(function(button) {
        button.addEventListener('click', function() {
          currentServiceId = button.getAttribute('data-service-id');
          var serviceName = button.getAttribute('data-service-name');

          if (deleteServiceNameDisplay && serviceName) {
            deleteServiceNameDisplay.textContent = serviceName;
          }
        });
      });

      confirmDeleteButton.addEventListener('click', function() {
        if (currentServiceId) {
          var orgId = window.location.pathname.split('/')[2];
          deleteForm.action = '/organizations/' + encodeURIComponent(orgId) + '?action=delete-service&service_id=' + encodeURIComponent(currentServiceId);

          deleteForm.submit();
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    initForms();
    initEditServiceConfirmation();
    initDeleteServiceConfirmation();
  });

  window.OrganizationDashboard = {
    highlightAndScrollToService: highlightAndScrollToService
  };
})(window);
