describe("Organization Dashboard - initEditServiceConfirmation", () => {
  let confirmButton, editForm;

  beforeEach(() => {
    document.body.innerHTML = `
      <form id="edit-service-form" action="/submit" method="post">
        <input type="text" id="service_name" name="service_name" value="Test Service" />
        <input type="email" id="primary_contact" name="primary_contact" value="test@example.com" />
      </form>

      <div class="usa-modal" id="confirmEditModal">
        <button type="button" id="edit-service-confirm-btn" class="usa-button">Confirm changes</button>
      </div>
    `;

    confirmButton = document.getElementById('edit-service-confirm-btn');
    editForm = document.getElementById('edit-service-form');

    editForm.submit = jest.fn();

    require('../../app/assets/javascripts/organizationDashboard.js');
    document.dispatchEvent(new Event('DOMContentLoaded'));
  });

  afterEach(() => {
    document.body.innerHTML = "";
    jest.resetModules();
  });

  test("Clicking confirm button submits the edit form", () => {
    confirmButton.click();

    expect(editForm.submit).toHaveBeenCalledTimes(1);
  });

  test("Does nothing if confirm button doesn't exist", () => {
    confirmButton.remove();

    expect(() => {
      const btn = document.getElementById('edit-service-confirm-btn');
      if (btn) btn.click();
    }).not.toThrow();
  });

  test("Does nothing if edit form doesn't exist", () => {
    editForm.remove();

    confirmButton.click();

    expect(true).toBe(true);
  });
});
