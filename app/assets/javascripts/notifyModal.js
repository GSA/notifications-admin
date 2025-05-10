let activeModal = null;
let lastFocusedElement = null;

function openModal(modalId) {
  const wrapper = document.getElementById(modalId);
  if (!wrapper) return;

  const modal = wrapper.querySelector('.usa-modal, dialog');
  if (!modal) return;

  lastFocusedElement = document.activeElement;

  wrapper.classList.remove('is-hidden');
  modal.removeAttribute('aria-hidden');
  modal.removeAttribute('inert');
  modal.removeAttribute('hidden');
  document.body.classList.add('modal-open');


  // Set focus to the first focusable element inside modal
  const focusTarget = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusTarget) focusTarget.focus();

  modal.addEventListener('keydown', function(e) {
    if (e.key !== 'Tab') return;

    const focusableElements = modal.querySelectorAll(
      'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  });

  activeModal = wrapper;
}

function closeModal() {
  if (!activeModal) return;

  const modal = activeModal.querySelector('.usa-modal, dialog');
  if (modal) {
    modal.setAttribute('aria-hidden', 'true');
    modal.setAttribute('inert', '');
    modal.setAttribute('hidden', '');
  }

  activeModal.classList.add('is-hidden');
  document.body.classList.remove('modal-open');

  if (lastFocusedElement) lastFocusedElement.focus();

  activeModal = null;

}

function attachModalTriggers() {
  document.querySelectorAll('[data-open-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-open-modal');
      openModal(modalId);
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      closeModal();
    });
  });
}

// Escape key closes modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && activeModal) {
    closeModal();
  }
});

// Optional: click outside modal closes it
document.addEventListener('click', (e) => {
  if (activeModal && e.target.classList.contains('usa-modal-overlay')) {
    closeModal();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  attachModalTriggers();
});

// ✅ Check if we're in a Node.js environment (for Jest) before using `module.exports`
if (typeof module !== "undefined" && typeof module.exports !== "undefined") {
  module.exports = { closeModal, openModal, attachModalTriggers };
}
