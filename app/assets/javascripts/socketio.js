function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

document.addEventListener("DOMContentLoaded", function () {
  const isJobPage = window.location.pathname.includes("/jobs/");
  if (!isJobPage) return;

  const jobEl = document.querySelector("[data-job-id]");
  const jobId = jobEl?.dataset?.jobId;
  const featureEnabled = jobEl?.dataset?.feature === "true";

  if (!jobId) return;


  if (featureEnabled) {
    const socket = io("http://localhost:6011");

    socket.on("connect", () => {
      console.log("Connected to Socket.IO server");
      socket.emit("join", { room: `job-${jobId}` });
      console.log("join", { room: `job-${jobId}` });
    });

    window.addEventListener("beforeunload", () => {
      socket.emit("leave", { room: `job-${jobId}` });
    });

    const debouncedUpdate = debounce((data) => {
      updateAllJobSections();
    }, 1000);

    socket.on("job_updated", (data) => {
      if (data.job_id !== jobId) return;
      debouncedUpdate(data);
    });
  }

  function updateAllJobSections() {
    const resourceEl = document.querySelector('[data-socket-update="status"]');
    const url = resourceEl?.dataset?.resource;

    if (!url) {
      console.warn("No resource URL found for job updates");
      return;
    }

    fetch(url)
      .then((res) => res.json())
      .then(({ status, counts, notifications }) => {
        const sections = {
          status: document.querySelector('[data-socket-update="status"]'),
          counts: document.querySelector('[data-socket-update="counts"]'),
          notifications: document.querySelector('[data-socket-update="notifications"]'),
        };

        if (status && sections.status) {
          sections.status.innerHTML = status;
          console.log("status partial updated");
        }
        if (counts && sections.counts) {
          sections.counts.innerHTML = counts;
          console.log("counts partial updated");
        }
        if (notifications && sections.notifications) {
          sections.notifications.innerHTML = notifications;
          console.log("notifications partial updated");
        }
      })
      .catch((err) => {
        console.error("Error fetching job update partials:", err);
      });
  }


});
