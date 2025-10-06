// Expose jQuery and other libraries to window for legacy code
if (typeof jQuery !== 'undefined') {
  window.jQuery = window.$ = jQuery;
}
if (typeof getCaretCoordinates !== 'undefined') {
  window.getCaretCoordinates = getCaretCoordinates;
}
