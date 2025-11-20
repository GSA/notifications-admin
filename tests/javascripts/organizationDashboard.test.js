/**
 * @jest-environment jsdom
 */

describe('organizationDashboard.js', () => {
  let originalLocation;

  beforeEach(() => {
    jest.resetModules();
    jest.useFakeTimers();

    originalLocation = window.location;
    Element.prototype.scrollIntoView = jest.fn();
    window.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 0));
  });

  afterEach(() => {
    jest.useRealTimers();
    document.body.innerHTML = '';
  });


  describe('Edit Service Confirmation', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <button id="edit-service-confirm-btn">Confirm Edit</button>
        <form id="edit-service-form"></form>
      `;

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));
    });

    test('submits edit form when confirm button clicked', () => {
      const confirmButton = document.getElementById('edit-service-confirm-btn');
      const editForm = document.getElementById('edit-service-form');
      editForm.submit = jest.fn();

      confirmButton.click();

      expect(editForm.submit).toHaveBeenCalled();
    });
  });

  describe('Form Initialization', () => {
    test('scrolls to and focuses create service form', () => {
      document.body.innerHTML = `
        <form id="create-service-form">
          <input type="text" name="service-name" />
        </form>
      `;

      const form = document.getElementById('create-service-form');
      const input = form.querySelector('input[type="text"]');

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      jest.runAllTimers();

      expect(form.scrollIntoView).toHaveBeenCalled();
      expect(document.activeElement).toBe(input);
    });

    test('scrolls to and focuses invite user form', () => {
      document.body.innerHTML = `
        <form id="invite-user-form">
          <input type="email" name="email" />
        </form>
      `;

      const form = document.getElementById('invite-user-form');
      const input = form.querySelector('input[type="email"]');

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      jest.runAllTimers();

      expect(form.scrollIntoView).toHaveBeenCalled();
      expect(document.activeElement).toBe(input);
    });

    test('scrolls to and focuses edit service form', () => {
      document.body.innerHTML = `
        <form id="edit-service-form">
          <input type="text" name="service-name" />
        </form>
      `;

      const form = document.getElementById('edit-service-form');
      const input = form.querySelector('input[type="text"]');

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      jest.runAllTimers();

      expect(form.scrollIntoView).toHaveBeenCalled();
      expect(document.activeElement).toBe(input);
    });

    test('does nothing when no relevant forms present', () => {
      document.body.innerHTML = '<div>No forms here</div>';

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      jest.runAllTimers();

      expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
    });
  });

  describe('Service Highlighting', () => {
    test('scrolls to and removes highlight from service', () => {
      document.body.innerHTML = `
        <div id="service-test-123" class="is-highlighted"></div>
      `;

      const serviceRow = document.getElementById('service-test-123');

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      window.OrganizationDashboard.highlightAndScrollToService('test-123');

      jest.advanceTimersByTime(300);
      expect(serviceRow.scrollIntoView).toHaveBeenCalled();

      expect(serviceRow.classList.contains('is-highlighted')).toBe(true);

      jest.advanceTimersByTime(3100);
      expect(serviceRow.classList.contains('is-highlighted')).toBe(false);
    });

    test('removes class attribute when empty after highlight removal', () => {
      document.body.innerHTML = `
        <div id="service-test-123" class="is-highlighted"></div>
      `;

      const serviceRow = document.getElementById('service-test-123');

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      window.OrganizationDashboard.highlightAndScrollToService('test-123');

      jest.advanceTimersByTime(3400);
      expect(serviceRow.hasAttribute('class')).toBe(false);
    });

    test('handles missing service element gracefully', () => {
      document.body.innerHTML = '<div>No service here</div>';

      require('../../app/assets/javascripts/organizationDashboard.js');
      document.dispatchEvent(new Event('DOMContentLoaded'));

      expect(() => {
        window.OrganizationDashboard.highlightAndScrollToService('nonexistent');
        jest.runAllTimers();
      }).not.toThrow();
    });
  });
});
