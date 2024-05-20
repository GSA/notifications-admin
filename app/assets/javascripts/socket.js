
(function (window) {
    document.addEventListener('DOMContentLoaded', (event) => {
        var socket = io();

        socket.on('connect', function() {
            console.log('Connected to the server');
        });

        socket.on('message', function(msg) {
            var li = document.createElement("li");
            li.appendChild(document.createTextNode(msg));
            document.getElementById("messages").appendChild(li);
        });

        document.getElementById('sendButton').addEventListener('click', function() {
            var message = document.getElementById("message").value;
            socket.send(message);
            document.getElementById("message").value = '';
        });
    });

})(window);
