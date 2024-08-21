// Ensure your filterTable function is defined and accessible in your test environment
beforeEach(() => {
    document.body.innerHTML = `
    <section aria-label="All activity search" class="margin-top-2">
        <form class="usa-search usa-search--small table-filter" role="search">
            <label class="usa-label margin-top-0" for="all-activity-search">Search</label>
            <input class="usa-input" id="all-activity-search" type="search" name="All activity search"/>
        </form>
    </section>
    <div class="usa-table-container--scrollable-mobile">
        <table class="usa-table usa-table--compact job-table">
            <thead class="table-field-headings">
                <tr>
                    <th scope="col" class="table-field-heading-first" id="jobId"><span>Job ID#</span></th>
                    <th scope="col" class="table-field-heading"><span>Template</span></th>
                    <th scope="col" class="table-field-heading"><span>Time sent</span></th>
                    <th scope="col" class="table-field-heading"><span>Sender</span></th>
                    <th scope="col" class="table-field-heading"><span>Report</span></th>
                    <th scope="col" class="table-field-heading"><span>Delivered</span></th>
                    <th scope="col" class="table-field-heading"><span>Failed</span></th>
                </tr>
            </thead>
            <tbody>
                <tr class="table-row" style="display: table-row;">
                    <td class="table-field jobid"><a href="#">Job 1</a></td>
                    <td class="table-field template">Template 1</td>
                    <td class="table-field time-sent">2024-08-20 10:00</td>
                    <td class="table-field sender">Sender 1</td>
                    <td class="table-field report"><a href="#"><img src="#" alt="File Download Icon"></a></td>
                    <td class="table-field delivered">10</td>
                    <td class="table-field failed">2</td>
                </tr>
                <tr class="table-row" style="display: table-row;">
                    <td class="table-field jobid"><a href="#">Job 2</a></td>
                    <td class="table-field template">Template 2</td>
                    <td class="table-field time-sent">2024-08-20 11:00</td>
                    <td class="table-field sender">Sender 2</td>
                    <td class="table-field report"><a href="#"><img src="#" alt="File Download Icon"></a></td>
                    <td class="table-field delivered">5</td>
                    <td class="table-field failed">0</td>
                </tr>
                <tr class="table-row" style="display: table-row;">
                    <td class="table-field jobid"><a href="#">Job 3</a></td>
                    <td class="table-field template">Template 3</td>
                    <td class="table-field time-sent">2024-08-20 12:00</td>
                    <td class="table-field sender">Sender 3</td>
                    <td class="table-field report"><a href="#"><img src="#" alt="File Download Icon"></a></td>
                    <td class="table-field delivered">0</td>
                    <td class="table-field failed">1</td>
                </tr>
            </tbody>
        </table>
        <div class="usa-table__announcement-region usa-sr-only" aria-live="polite" aria-atomic="true">
            <!-- Live region content goes here -->
        </div>
    </div>
    `;

    // Attach the filterTable function to the window object for testing
    window.filterTable = function() {
        const searchInput = document.getElementById('all-activity-search');
        const tableRows = document.querySelectorAll('.job-table tbody .table-row');
        const tableBody = document.querySelector('.job-table tbody');
        const liveRegion = document.querySelector('.usa-table__announcement-region');

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
    };
});

test('filterTable function filters rows based on input', () => {
    const searchInput = document.getElementById('all-activity-search');
    searchInput.value = 'Job 2';

    // Call the filterTable function directly
    window.filterTable();

    const tableRows = document.querySelectorAll('.job-table tbody .table-row');
    expect(getComputedStyle(tableRows[0]).display).toBe('none');
    expect(getComputedStyle(tableRows[1]).display).toBe('table-row');
    expect(getComputedStyle(tableRows[2]).display).toBe('none');

    const liveRegion = document.querySelector('.usa-table__announcement-region');
    expect(liveRegion.textContent).toBe('1 result found');
});

test('filterTable function shows "No results found" when no rows match', () => {
    const searchInput = document.getElementById('all-activity-search');
    searchInput.value = 'Non-existent Job';

    // Call the filterTable function directly
    window.filterTable();

    const tableRows = document.querySelectorAll('.job-table tbody .table-row');
    tableRows.forEach(row => {
        expect(getComputedStyle(row).display).toBe('none');
    });

    const noResultsRow = document.querySelector('.no-results');
    expect(noResultsRow).not.toBeNull();
    expect(noResultsRow.textContent.trim()).toBe('No results found');

    const liveRegion = document.querySelector('.usa-table__announcement-region');
    expect(liveRegion.textContent).toBe('0 results found');
});

test('filterTable function filters rows only after 2 characters are entered', () => {
    const searchInput = document.getElementById('all-activity-search');
    const tableRows = document.querySelectorAll('.job-table tbody .table-row');

    // Set input value to 1 character and run filterTable
    searchInput.value = 'J';
    window.filterTable();

    // Expect all rows to still be visible
    tableRows.forEach(row => {
        expect(getComputedStyle(row).display).toBe('table-row');
    });

    // Set input value to 2 characters and run filterTable
    searchInput.value = 'Jo';
    window.filterTable();

    // Expect filtering to take place
    expect(getComputedStyle(tableRows[0]).display).toBe('table-row');
    expect(getComputedStyle(tableRows[1]).display).toBe('table-row');
    expect(getComputedStyle(tableRows[2]).display).toBe('table-row');

    // Set input value to filter down to one row
    searchInput.value = 'Job 2';
    window.filterTable();

    // Expect only the second row to be visible
    expect(getComputedStyle(tableRows[0]).display).toBe('none');
    expect(getComputedStyle(tableRows[1]).display).toBe('table-row');
    expect(getComputedStyle(tableRows[2]).display).toBe('none');
});

test('filterTable function shows "No results found" when no rows match after 2 characters', () => {
    const searchInput = document.getElementById('all-activity-search');
    searchInput.value = 'Non-existent Job';

    // Call the filterTable function directly
    window.filterTable();

    const tableRows = document.querySelectorAll('.job-table tbody .table-row');
    tableRows.forEach(row => {
        expect(getComputedStyle(row).display).toBe('none');
    });

    const noResultsRow = document.querySelector('.no-results');
    expect(noResultsRow).not.toBeNull();
    expect(noResultsRow.textContent.trim()).toBe('No results found');

    const liveRegion = document.querySelector('.usa-table__announcement-region');
    expect(liveRegion.textContent).toBe('0 results found');
});
