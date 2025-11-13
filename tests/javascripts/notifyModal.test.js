/**
 * @jest-environment jsdom
 */

const { openModal, closeModal, attachModalTriggers } = require("../../app/assets/javascripts/notifyModal.js"); // adjust path if needed

describe("Modal functionality", () => {
  let modalWrapper, modalElement, openBtn, closeBtn, anotherFocusable;

  beforeEach(() => {
    document.body.innerHTML = `
      <button data-open-modal="myModal">Open Modal</button>

      <div id="myModal" class="is-hidden">
        <div class="usa-modal">
          <div class="usa-modal-overlay">
            <div class="usa-modal-content">
              <button data-close-modal>Close</button>
              <a href="#">Focusable Link</a>
              <input type="text" />
            </div>
          </div>
        </div>
      </div>
    `;

    modalWrapper = document.getElementById("myModal");
    modalElement = modalWrapper.querySelector(".usa-modal");
    openBtn = document.querySelector('[data-open-modal]');
    closeBtn = modalWrapper.querySelector('[data-close-modal]');
    anotherFocusable = modalWrapper.querySelector('a');
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  test("Opens the modal and sets focus to the first focusable element", () => {
    document.activeElement.blur(); // ensure focus starts elsewhere
    openModal("myModal");

    expect(modalWrapper.classList.contains("is-hidden")).toBe(false);
    expect(modalElement.hasAttribute("aria-hidden")).toBe(false);
    expect(modalElement.hasAttribute("inert")).toBe(false);
    expect(modalElement.hasAttribute("hidden")).toBe(false);
    expect(document.body.classList.contains("modal-open")).toBe(true);
    expect(document.activeElement).toBe(closeBtn);
  });

  test("Closes the modal and restores focus", () => {
    openBtn.focus();
    openModal("myModal");
    closeModal();

    expect(modalWrapper.classList.contains("is-hidden")).toBe(true);
    expect(modalElement.getAttribute("aria-hidden")).toBe("true");
    expect(modalElement.hasAttribute("inert")).toBe(true);
    expect(modalElement.hasAttribute("hidden")).toBe(true);
    expect(document.body.classList.contains("modal-open")).toBe(false);
    expect(document.activeElement).toBe(openBtn);
  });

  test("Closes the modal when pressing Escape", () => {
    openModal("myModal");

    const event = new KeyboardEvent("keydown", { key: "Escape" });
    document.dispatchEvent(event);

    expect(modalWrapper.classList.contains("is-hidden")).toBe(true);
  });

  test("Traps focus within the modal when Tab is pressed", () => {
    openModal("myModal");

    const focusableElements = modalElement.querySelectorAll(
      'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    focusableElements[focusableElements.length - 1].focus(); // Last element

    const tabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true
    });

    modalElement.dispatchEvent(tabEvent);
    expect(document.activeElement).toBe(focusableElements[0]);
  });

  test("Traps focus backwards when Shift+Tab is pressed from first element", () => {
    openModal("myModal");

    const focusableElements = modalElement.querySelectorAll(
      'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    focusableElements[0].focus(); // First element

    const shiftTabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: true,
      bubbles: true
    });

    modalElement.dispatchEvent(shiftTabEvent);
    expect(document.activeElement).toBe(focusableElements[focusableElements.length - 1]);
  });

  test("Closes modal when clicking on overlay", () => {
    openModal("myModal");
    const overlay = modalElement.querySelector(".usa-modal-overlay");

    const clickEvent = new MouseEvent("click", {
      bubbles: true
    });

    overlay.dispatchEvent(clickEvent);
    expect(modalWrapper.classList.contains("is-hidden")).toBe(true);
  });
});

describe("Modal trigger buttons", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <button data-open-modal="myModal">Open Modal</button>
        <div id="myModal" class="is-hidden">
          <div class="usa-modal">
            <div class="usa-modal-content">
              <button data-close-modal>Close</button>
            </div>
          </div>
        </div>
      `;
    });

    afterEach(() => {
      document.body.innerHTML = "";
    });

    test("Clicking [data-open-modal] opens the modal", () => {
      attachModalTriggers();
      const openButton = document.querySelector('[data-open-modal]');
      openButton.click();

      const modalWrapper = document.getElementById("myModal");
      expect(modalWrapper.classList.contains("is-hidden")).toBe(false);
    });

    test("Clicking [data-close-modal] closes the modal", () => {
      const modalWrapper = document.getElementById("myModal");
      modalWrapper.classList.remove("is-hidden");

      attachModalTriggers();
      const closeButton = document.querySelector('[data-close-modal]');
      closeModal(); // ensure modal is open to begin with
      openModal("myModal");

      closeButton.click();
      expect(modalWrapper.classList.contains("is-hidden")).toBe(true);
    });
  });

describe("Modal edge cases", () => {
  test("openModal does nothing if wrapper doesn't exist", () => {
    expect(() => {
      openModal("nonExistentModal");
    }).not.toThrow();
  });

  test("openModal does nothing if modal element doesn't exist inside wrapper", () => {
    document.body.innerHTML = `<div id="emptyWrapper"></div>`;
    expect(() => {
      openModal("emptyWrapper");
    }).not.toThrow();
  });

  test("openModal works when there is no focusable element", () => {
    document.body.innerHTML = `
      <div id="noFocusModal">
        <div class="usa-modal">
          <p>No focusable elements here</p>
        </div>
      </div>
    `;
    expect(() => {
      openModal("noFocusModal");
    }).not.toThrow();
    expect(document.getElementById("noFocusModal").classList.contains("is-hidden")).toBe(false);
  });

  test("closeModal does nothing if no modal is active", () => {
    expect(() => {
      closeModal();
    }).not.toThrow();
  });

  test("closeModal handles case where modal element is missing", () => {
    document.body.innerHTML = `
      <button data-open-modal="testModal">Open</button>
      <div id="testModal"></div>
    `;
    openModal("testModal");
    expect(() => {
      closeModal();
    }).not.toThrow();
  });

  test("Modal keydown handler ignores non-Tab keys", () => {
    document.body.innerHTML = `
      <div id="keyModal">
        <div class="usa-modal">
          <button>Test</button>
        </div>
      </div>
    `;
    openModal("keyModal");
    const modal = document.querySelector(".usa-modal");

    const enterEvent = new KeyboardEvent("keydown", {
      key: "Enter",
      bubbles: true
    });

    expect(() => {
      modal.dispatchEvent(enterEvent);
    }).not.toThrow();
  });
});
