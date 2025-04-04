const socket = io('http://localhost:6011');
const jobId = document.querySelector("[data-job-id]").dataset.jobId;


  socket.on('connect', () => {
    console.log('✅ Connected to server');
  });

  socket.on('job_update', (data) => {
    console.log('📡 Received job update:', data);

    if (data.job_id === jobId) {
      document.getElementById('status').innerText = `Job ${data.job_id}: ${data.status}`;
    }
  });
