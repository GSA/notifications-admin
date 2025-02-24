// document.addEventListener("DOMContentLoaded", function () {
//     const form = document.querySelector(".send-one-off-form");
//     const phoneInput = document.getElementById("phone-number");

//     // Try to get the error element
//     let phoneError = document.getElementById("phone-number-error");

//     // If not found, create it
//     if (!phoneError) {
//       phoneError = document.createElement("span");
//       phoneError.id = "phone-number-error";
//       phoneError.classList.add("usa-error-message");
//       phoneError.style.display = "none"; // Keep it hidden initially
//       phoneInput.insertAdjacentElement("afterend", phoneError);
//     }

//     form.addEventListener("submit", function (event) {
//       let isValid = true;

//       if (phoneInput.value.trim() === "") {
//         showError(phoneInput, phoneError, "Phone number cannot be empty.");
//         isValid = false;
//       }

//       if (!isValid) event.preventDefault();
//     });

//     // Remove error when user starts typing
//     phoneInput.addEventListener("input", function () {
//       if (phoneInput.value.trim() !== "") {
//         hideError(phoneInput, phoneError);
//       }
//     });

//     function showError(input, errorElement, message) {
//       errorElement.textContent = message;
//       errorElement.style.display = "block";
//       input.classList.add("usa-input--error");
//       input.setAttribute("aria-describedby", errorElement.id);
//     }

//     function hideError(input, errorElement) {
//       errorElement.style.display = "none";
//       input.classList.remove("usa-input--error");
//       input.removeAttribute("aria-describedby");
//     }
//   });
