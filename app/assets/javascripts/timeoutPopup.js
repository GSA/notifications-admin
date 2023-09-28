(function(global) {
    "use strict";

    const sessionTimer = document.getElementById("sessionTimer");

    function checkTimer(timeTillSessionEnd) {
        var now = new Date().getTime();
        var difference = timeTillSessionEnd - now;
        var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((difference % (1000 * 60)) / 1000);
        document.getElementById("timeLeft").innerHTML = + minutes + "m " + seconds + "s";
        showTimer();
        document.getElementById("logOutTimer").addEventListener("click", logoutUser);
        document.getElementById("extendSessionTimer").addEventListener("click", extendSession);
        if (difference < 0) {
            clearInterval(x);
            closeTimer();
            logoutUser();
        }
    }

    function logoutUser() {
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

    global.GOVUK.Modules.TimeoutPopup = function() {
        setTimeout(function() {
            var timeTillSessionEnd = new Date().getTime() + (5 * 60 * 1000);
            var x = setInterval(checkTimer, 1000, timeTillSessionEnd);
        }, 25 * 60 * 1000);
    };

    global.GOVUK.Modules.TimeoutPopup.checkTimer = checkTimer;
    global.GOVUK.Modules.TimeoutPopup.logoutUser = logoutUser;
    global.GOVUK.Modules.TimeoutPopup.extendSession = extendSession;
    global.GOVUK.Modules.TimeoutPopup.showTimer = showTimer;
    global.GOVUK.Modules.TimeoutPopup.closeTimer = closeTimer;
})(window);
