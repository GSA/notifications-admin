(function(global ) {
    "use strict";

    var cookie = window.GOVUK.getCookie('notify_admin_session');

    if (cookie) {
        window.alert("Session will expire: Cookie Value" + cookie);
    } else {
        window.alert('Session has expired');
    }
    console.log(cookie);


})(window);

