function showError(input, errorElement, message) {
    errorElement.textContent = ""; // Clear existing message
    errorElement.style.display = "block";

    // Small delay to ensure screen readers pick up the change
    setTimeout(() => {
        errorElement.textContent = message;
    }, 10);

    if (input.type !== "radio" && input.type !== "checkbox") {
        input.classList.add("usa-input--error");
    }
    input.setAttribute("aria-describedby", errorElement.id);
}

function hideError(input, errorElement) {
    errorElement.style.display = "none";
    if (input.type !== "radio" && input.type !== "checkbox") {
        input.classList.remove("usa-input--error");
    }
    input.removeAttribute("aria-describedby");
}

function getFieldLabel(input) {
    const label = document.querySelector(`label[for="${input.id}"]`);
    return label ? label.textContent.trim() : "This field";
}

// Attach validation logic to forms
function attachValidation() {
    const forms = document.querySelectorAll('form[data-force-focus="True"]');
    forms.forEach((form) => {
        const inputs = form.querySelectorAll("input, textarea, select");

        form.addEventListener("submit", function (event) {
            let isValid = true;
            let firstInvalidInput = null;
            const validatedRadioNames = new Set();

            inputs.forEach((input) => {
                const errorId = input.id ? `${input.id}-error` : `${input.name}-error`;
                let errorElement = document.getElementById(errorId);

                if (!errorElement) {
                    errorElement = document.createElement("span");
                    errorElement.id = errorId;
                    errorElement.classList.add("usa-error-message");
                    errorElement.setAttribute("aria-live", "polite");
                    if (input.type === "radio") {
                        const group = form.querySelectorAll(`input[name="${input.name}"]`);
                        const lastRadio = group[group.length - 1];
                        lastRadio.parentElement.insertAdjacentElement("afterend", errorElement);
                      } else {
                        input.insertAdjacentElement("afterend", errorElement);
                      }                }

                if (input.type === "radio") {
                    if (validatedRadioNames.has(input.name)) {
                        return; // already validated this group
                      }
                      validatedRadioNames.add(input.name);
                    // Find all radio buttons with the same name
                    const radioGroup = document.querySelectorAll(`input[name="${input.name}"]`);
                    const isChecked = Array.from(radioGroup).some(radio => radio.checked);

                    if (!isChecked) {
                        showError(input, errorElement, `Error: A selection must be made.`);
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
                const errorElement = document.getElementById(input.id ? `${input.id}-error` : `${input.name}-error`);
                if (errorElement && input.value.trim() !== "") {
                    hideError(input, errorElement);
                }
            });

            if (input.type === "radio") {
                input.addEventListener("change", function () {
                    console.log(`Radio ${input.id} changed`);

                    const groupError = document.getElementById(`${input.name}-error`)
                        || document.getElementById(`${input.id}-error`);
                    if (groupError) hideError(input, groupError);
                });
            }
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
