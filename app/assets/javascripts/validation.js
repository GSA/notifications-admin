function showError(input, errorElement, message) {
    errorElement.textContent = ""; // Clear existing message
    errorElement.style.display = "block";

    // Small delay to ensure screen readers pick up the change
    setTimeout(() => {
        errorElement.textContent = message;
    }, 10);

    input.classList.add("usa-input--error");
    input.setAttribute("aria-describedby", errorElement.id);
}

function hideError(input, errorElement) {
    errorElement.style.display = "none";
    input.classList.remove("usa-input--error");
    input.removeAttribute("aria-describedby");
}

function getFieldLabel(input) {
    const label = document.querySelector(`label[for="${input.id}"]`);
    return label ? label.textContent.trim() : "This field";
}

// Attach validation logic to forms
function attachValidation() {
    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
        const inputs = form.querySelectorAll("input, textarea, select");

        form.addEventListener("submit", function (event) {
            let isValid = true;
            let firstInvalidInput = null;

            inputs.forEach((input) => {
                const errorId = input.id ? `${input.id}-error` : `${input.name}-error`;
                let errorElement = document.getElementById(errorId);

                if (!errorElement) {
                    errorElement = document.createElement("span");
                    errorElement.id = errorId;
                    errorElement.classList.add("usa-error-message");
                    errorElement.setAttribute("aria-live", "polite");
                    input.insertAdjacentElement("afterend", errorElement);
                }

                if (input.type === "radio") {
                    // Find all radio buttons with the same name
                    const radioGroup = document.querySelectorAll(`input[name="${input.name}"]`);
                    const isChecked = Array.from(radioGroup).some(radio => radio.checked);

                    if (!isChecked) {
                        showError(input, errorElement, `Error: ${getFieldLabel(input)} must be selected.`);
                        isValid = false;
                        if (!firstInvalidInput) {
                            firstInvalidInput = input;
                        }
                    }
                } else if (input.value.trim() === "") {
                    showError(input, errorElement, `Error: ${getFieldLabel(input)} is required.`);
                    isValid = false;
                    if (!firstInvalidInput) {
                        firstInvalidInput = input;
                    }
                }
            });

            if (!isValid) {
                event.preventDefault();
                if (firstInvalidInput) firstInvalidInput.focus();
            }
        });

        inputs.forEach((input) => {
            input.addEventListener("input", function () {
                const errorElement = document.getElementById(`${input.id}-error`);
                if (input.value.trim() !== "" && errorElement) {
                    hideError(input, errorElement);
                }
            });
        });
    });
}

// Automatically attach validation only in the browser
if (typeof window !== "undefined") {
    document.addEventListener("DOMContentLoaded", attachValidation);
}

// ✅ Check if we're in a Node.js environment (for Jest) before using `module.exports`
if (typeof module !== "undefined" && typeof module.exports !== "undefined") {
    module.exports = { showError, hideError, getFieldLabel, attachValidation };
}
