document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('activity-search');
    const tableRows = document.querySelectorAll('.job-table tbody .table-row');
    const tableBody = document.querySelector('.job-table tbody');
    const liveRegion = document.querySelector('.usa-table__announcement-region');

    function filterTable() {
        const filter = searchInput.value.toLowerCase();
        let visibleRowCount = 0;

        tableRows.forEach(row => {
            const rowText = row.textContent.toLowerCase();

            if (rowText.includes(filter)) {
                row.style.display = 'table-row'; // Show the row
                visibleRowCount++;
            } else {
                row.style.display = 'none'; // Hide the row
            }
        });

        // Update ARIA live region
        liveRegion.textContent = `${visibleRowCount} result${visibleRowCount !== 1 ? 's' : ''} found`;

        // Check if there are no visible rows
        if (visibleRowCount === 0) {
            let noResultsRow = document.querySelector('.no-results');
            if (!noResultsRow) {
                const newRow = document.createElement('tr');
                newRow.classList.add('no-results');
                newRow.innerHTML = `
                    <td colspan="7" class="table-empty-message">No results found</td>
                `;
                tableBody.appendChild(newRow);
            }
        } else {
            const noResultsRow = document.querySelector('.no-results');
            if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    }

    // Listen for input events to catch when the "X" button is used
    searchInput.addEventListener('input', function() {
        filterTable();
    });

    // Also handle the keyup event for other input changes
    searchInput.addEventListener('keyup', function() {
        filterTable();
    });
});
