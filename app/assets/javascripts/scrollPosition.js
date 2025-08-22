document.querySelectorAll('.usa-button-group a, .usa-pagination a').forEach(function(button) {
  button.addEventListener('click', function() {
    sessionStorage.setItem('scrollPosition', window.pageYOffset);
  });
});

document.addEventListener('DOMContentLoaded', function() {
  var scrollPosition = sessionStorage.getItem('scrollPosition');
  if (scrollPosition !== null) {
    window.scrollTo(0, parseInt(scrollPosition));
    sessionStorage.removeItem('scrollPosition');
  }
});
