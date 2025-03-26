const socket = io();
const jobId = document.querySelector("[data-job-id]").dataset.jobId;

socket.on('connect', () => {
  console.log('Connected to server');
});


  // Join a room
  socket.emit("join", { room: `job-${jobId}` });
  console.log("🧠 Joined room:", `job-${jobId}`);

  // Listen for job updates
  socket.on("job_update", function (data) {
    const el = document.querySelector(`[data-key="${data.key}"]`);
    if (el) {
      el.textContent = "✅ Real-time update success!";
      el.classList.add("text-success"); // Add a class instead
    }
  });
