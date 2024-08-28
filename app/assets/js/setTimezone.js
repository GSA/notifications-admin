document.addEventListener('DOMContentLoaded', function() {
    var timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    document.cookie = `timezone=${timeZone}; path=/`;
})
