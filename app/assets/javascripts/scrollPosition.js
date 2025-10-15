document.querySelectorAll('.usa-button-group a, .usa-pagination a').forEach(function(button) {
  button.addEventListener('click', function(e) {
    // Add scroll position to URL as fragment
    var scrollPos = window.pageYOffset;
    if (scrollPos > 0) {
      var url = new URL(this.href, window.location.href);
      url.hash = 'scroll=' + scrollPos;
      this.href = url.toString();
    }
  });
});

document.addEventListener('DOMContentLoaded', function() {
  var hash = window.location.hash;
  if (hash && hash.startsWith('#scroll=')) {
    var scrollPosition = parseInt(hash.substring(8), 10);
    if (!isNaN(scrollPosition) && scrollPosition > 0) {
      window.scrollTo(0, scrollPosition);
      // Clean up the URL
      if (window.history && window.history.replaceState) {
        var cleanUrl = window.location.pathname + window.location.search;
        window.history.replaceState(null, '', cleanUrl);
      }
    }
  }
});
