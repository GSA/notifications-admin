(function(global) {
    "use strict";

    const sessionTimer = document.getElementById("sessionTimer");

    setTimeout(function() {
        var timeTillSessionEnd = new Date().getTime() + (5 * 60 * 1000);
        var x = setInterval(function() {
            var now = new Date().getTime();
            var difference = timeTillSessionEnd - now;
            var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((difference % (1000 * 60)) / 1000);
            document.getElementById("timerWarning").innerHTML = "You have been inactive " +
                "for too long. Please choose to stay signed in or sign out. Your session will " +
                "expire in " + minutes + "m " + seconds + "s ";
            showTimer();
            document.getElementById("logOutTimer").addEventListener("click", logoutByUser);
            document.getElementById("extendSessionTimer").addEventListener("click", extendSession);
            if (difference < 0) {
                clearInterval(x);
                closeTimer();
                redirectToSignin();
            }
        }, 1000);
    }, 60 * 1000);

    function redirectToSignin() {
        window.location.href = '/sign-in';
    }

    function logoutByUser() {
        window.location.href = '/sign-out';
    }

    function extendSession() {
        window.location.reload();
    }

    function showTimer() {
        sessionTimer.showModal();
    }

    function closeTimer() {
        sessionTimer.close();
    }

})(window);
