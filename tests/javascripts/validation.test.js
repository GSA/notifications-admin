const { showError, hideError, getFieldLabel, attachValidation } = require("../../app/assets/javascripts/validation.js");

describe("Form Validation", () => {
  let form, input, submitButton;

  beforeEach(() => {
    document.body.innerHTML = `
      <form class="send-one-off-form" data-force-focus="True">
        <label for="test-input">Test Input</label>
        <input id="test-input" name="testInput" type="text" />
        <button type="submit">Submit</button>
      </form>
    `;

    form = document.querySelector('form[data-force-focus="True"]');
    input = document.getElementById("test-input");
    submitButton = form.querySelector("button");

    // Manually attach validation logic for Jest
    attachValidation();
  });

  afterEach(() => {
    document.body.innerHTML = ""; // Clean up DOM after each test
  });

  test("Displays an error message when input is empty", async () => {
    form.dispatchEvent(new Event("submit", { bubbles: true }));

    // Wait for the timeout to complete
    await new Promise(resolve => setTimeout(resolve, 20));

    const errorMessage = document.getElementById("test-input-error");
    expect(errorMessage).not.toBeNull();
    expect(errorMessage.textContent).toBe("Error: Test Input is required.");
    expect(input.classList.contains("usa-input--error")).toBe(true);
});

  test("Removes error message when input is filled", () => {
    // Trigger validation first
    form.dispatchEvent(new Event("submit", { bubbles: true }));

    // Simulate user typing to remove the error
    input.value = "Some text";
    input.dispatchEvent(new Event("input", { bubbles: true }));

    const errorMessage = document.getElementById("test-input-error");
    expect(errorMessage).not.toBeNull();
    expect(errorMessage.style.display).toBe("none");
    expect(input.classList.contains("usa-input--error")).toBe(false);
  });

  test("Focus moves to first invalid input", async () => {
    const spy = jest.spyOn(input, "focus");

    form.dispatchEvent(new Event("submit", { bubbles: true }));

    await new Promise((resolve) => setTimeout(resolve, 10)); // Allow DOM updates

    expect(spy).toHaveBeenCalled();
  });

  test("Displays error if no radio in group is selected", async () => {
    document.body.innerHTML = `
      <form class="send-one-off-form" data-force-focus="True">
        <fieldset>
          <legend>Pick one</legend>
          <input type="radio" id="opt1" name="group" value="1" />
          <label for="opt1">Option 1</label>
          <input type="radio" id="opt2" name="group" value="2" />
          <label for="opt2">Option 2</label>
          <button type="submit">Submit</button>
        </fieldset>
      </form>
    `;

    form = document.querySelector('form[data-force-focus="True"]');
    attachValidation();

    form.dispatchEvent(new Event("submit", { bubbles: true }));
    await new Promise(resolve => setTimeout(resolve, 20));

    const errorElement = document.getElementById("group-error");
    expect(errorElement).not.toBeNull();
    expect(errorElement.textContent).toBe("Error: A selection must be made.");
  });

  test("Removes radio group error when one is selected", async () => {
    document.body.innerHTML = `
      <form class="send-one-off-form" data-force-focus="True">
        <input type="radio" id="radio1" name="group" value="1" />
        <label for="radio1">Option 1</label>
        <input type="radio" id="radio2" name="group" value="2" />
        <label for="radio2">Option 2</label>
        <button type="submit">Submit</button>
      </form>
    `;

    form = document.querySelector('form[data-force-focus="True"]');
    attachValidation();

    form.dispatchEvent(new Event("submit", { bubbles: true }));
    await new Promise(resolve => setTimeout(resolve, 20));

    const radioInput = document.getElementById("radio2");
    radioInput.checked = true;
    radioInput.dispatchEvent(new Event("change", { bubbles: true }));

    const errorElement = document.getElementById("group-error");
    expect(errorElement.style.display).toBe("none");
  });

});
