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
                const errorId = input.type === "radio" ? `${input.name}-error` : `${input.id}-error`;
                let errorElement = document.getElementById(errorId);

                if (!errorElement) {
                    errorElement = document.createElement("span");
                    errorElement.id = errorId;
                    errorElement.classList.add("usa-error-message");
                    errorElement.setAttribute("aria-live", "polite");
                    errorElement.style.display = "none";
                    if (input.type === "radio") {
                        const group = form.querySelectorAll(`input[name="${input.name}"]`);
                        const lastRadio = group[group.length - 1];
                        lastRadio.parentElement.insertAdjacentElement("afterend", errorElement);
                    } else {
                        input.insertAdjacentElement("afterend", errorElement);
                    }
                }

                if (input.type === "radio") {
                    if (validatedRadioNames.has(input.name)) return;
                    validatedRadioNames.add(input.name);
                    const radioGroup = form.querySelectorAll(`input[name="${input.name}"]`);
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
                const errorId = input.type === "radio" ? `${input.name}-error` : `${input.id}-error`;
                const errorElement = document.getElementById(errorId);
                if (errorElement && input.value.trim() !== "") {
                    hideError(input, errorElement);
                }
            });
            if (input.type === "radio") {
                input.addEventListener("change", function () {
                    const errorElement = document.getElementById(`${input.name}-error`);
                    if (errorElement) {
                        hideError(input, errorElement);
                    }
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
