// Auto-refresh job statuses on downloads page
document.addEventListener('DOMContentLoaded', function() {
    const jobRows = document.querySelectorAll('[data-job-id]');
    jobRows.forEach(function(row) {
        const jobId = row.dataset.jobId;
        fetch(`/downloads/status/${jobId}`)
            .then(r => r.json())
            .then(data => {
                const statusCell = row.querySelector('.job-status');
                if (statusCell) {
                    statusCell.textContent = data.status;
                    if (data.status === 'running') {
                        statusCell.style.color = '#6d4aff';
                    }
                }
            })
            .catch(() => {});
    });
});