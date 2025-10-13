export function initCurrentYear() {
  const currentYearElement = document.getElementById("current-year");

  if (currentYearElement) {
    currentYearElement.textContent = new Date().getFullYear();
  }
}
