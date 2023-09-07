(function(global) {
    "use strict";
    hideTimerButtons();

    setTimeout(function() {
        var timeTillSessionEnd = new Date().getTime() + (5 * 60 * 1000);
        var x = setInterval(function() {
            var now = new Date().getTime();
            var difference = timeTillSessionEnd - now;
            var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((difference % (1000 * 60)) / 1000);

            document.getElementById("timerWarning").innerHTML = "Your session will " +
                "expire in " + minutes + "m " + seconds + "s ";
            showTimerButtons();
            document.getElementById("logOutTimer").addEventListener("click", logoutByUser);
            document.getElementById("extendSessionTimer").addEventListener("click", extendSession);
            if (difference === 0) {
                clearInterval(x);
                redirectToSignin();
            }
        }, 1000);
    }, 25 * 60 * 1000);

    function redirectToSignin() {
        window.location.href = '/sign-in';
    }

    function logoutByUser() {
        window.location.href = '/sign-out';
    }

    function extendSession() {
        window.location.reload();
    }

    function hideTimerButtons() {
        document.getElementById("logOutTimer").style.display = 'none';
        document.getElementById("extendSessionTimer").style.display = 'none';
    }

    function showTimerButtons() {
        document.getElementById("logOutTimer").style.display = 'block';
        document.getElementById("extendSessionTimer").style.display = 'block';
    }

})(window);
