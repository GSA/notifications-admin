
(function (window) {
    document.addEventListener('DOMContentLoaded', (event) => {
        var socket = io();

        socket.on('connect', function() {
            console.log('Connected to the server');
        });

        // Listen for job updates from the server
        socket.on('job_update', function(data) {
            console.log('Received job update:', data);
        });

        document.getElementById('fetchJobsButton').addEventListener('click', function() {
            const serviceId = 'b1226555-1f1a-472c-9086-043b0a69f4ec';  // Example service ID
            socket.emit('fetch_jobs', serviceId);
        });
    });

})(window);
