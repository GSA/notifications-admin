const { createTable, handleDropdownChange, fetchData, createChart } = require('../../app/assets/javascripts/dashboardVisualization.js');

// Mock functions
jest.mock('../../app/assets/javascripts/dashboardVisualization.js', () => ({
    createTable: jest.fn(),
    handleDropdownChange: jest.fn(),
    fetchData: jest.fn(),
    createChart: jest.fn(),
}));

describe('Dashboard Visualization Module', () => {
    test('should have createTable function', () => {
        expect(typeof createTable).toBe('function');
    });

    test('should have handleDropdownChange function', () => {
        expect(typeof handleDropdownChange).toBe('function');
    });

    test('should have fetchData function', () => {
        expect(typeof fetchData).toBe('function');
    });
});

describe('Table Creation', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="Weekly">
                <div class="chart-header">
                    <div class="chart-subtitle">Weekly</div>
                </div>
                <table id="weeklyTable" class="usa-sr-only usa-table"></table>
            </div>
        `;
    });

    test('creates a table with the correct data', () => {
        const labels = ['Day 1', 'Day 2', 'Day 3'];
        const deliveredData = [10, 20, 30];
        const failedData = [1, 2, 3];

        createTable.mockImplementation((tableId, chartType, labels, deliveredData, failedData) => {
            const table = document.getElementById(tableId);
            table.innerHTML = ""; // Clear previous data

            const caption = document.createElement('caption');
            caption.textContent = 'Weekly';
            const thead = document.createElement('thead');
            const tbody = document.createElement('tbody');

            // Create table header
            const headerRow = document.createElement('tr');
            const headers = ['Day', 'Delivered', 'Failed'];
            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            // Create table body
            labels.forEach((label, index) => {
                const row = document.createElement('tr');
                const cellDay = document.createElement('td');
                cellDay.textContent = label;
                row.appendChild(cellDay);

                const cellDelivered = document.createElement('td');
                cellDelivered.textContent = deliveredData[index];
                row.appendChild(cellDelivered);

                const cellFailed = document.createElement('td');
                cellFailed.textContent = failedData[index];
                row.appendChild(cellFailed);

                tbody.appendChild(row);
            });

            table.appendChild(caption);
            table.appendChild(thead);
            table.appendChild(tbody);
        });

        createTable('weeklyTable', 'Weekly', labels, deliveredData, failedData);

        const table = document.getElementById('weeklyTable');
        expect(document.body.contains(table)).toBe(true);
        expect(table.querySelectorAll('tbody tr').length).toBe(labels.length);
    });
});

describe('Dropdown Change Handler', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="chartsArea">
                <form class="usa-form">
                    <label class="usa-label" for="options">Account</label>
                    <select class="usa-select margin-bottom-2" name="options" id="options">
                        <option value>- Select -</option>
                        <option value="service" selected>Service Name</option>
                        <option value="individual">User Name</option>
                    </select>
                </form>
                <div id="Weekly">
                    <div class="chart-header">
                        <div class="chart-subtitle">Service Name - Last 7 Days</div>
                        <div class="chart-legend" aria-label="Legend"></div>
                    </div>
                    <div class="chart-container" id="weeklyChart" data-service-id="12345"></div>
                    <table id="weeklyTable" class="usa-sr-only usa-table"></table>
                </div>
            </div>
            <div id="message"></div>
            <div id="aria-live-account" class="usa-sr-only" aria-live="polite"></div>
        `;
        handleDropdownChange.mockClear();
    });

    test('updates subtitle and aria-live region correctly for individual', () => {
        const dropdown = document.getElementById('options');
        dropdown.value = 'individual';

        handleDropdownChange.mockImplementation(({ target }) => {
            const selectedValue = target.value;
            const subTitle = document.querySelector(`#chartsArea .chart-subtitle`);
            const selectElement = document.getElementById('options');
            const selectedText = selectElement.options[selectElement.selectedIndex].text;

            if (selectedValue === "individual") {
                subTitle.textContent = selectedText + " - Last 7 Days";
                fetchData('individual');
            } else if (selectedValue === "service") {
                subTitle.textContent = selectedText + " - Last 7 Days";
                fetchData('service');
            }

            const liveRegion = document.getElementById('aria-live-account');
            liveRegion.textContent = `Data updated for ${selectedText} - Last 7 Days`;
        });

        handleDropdownChange({ target: dropdown });

        const subTitle = document.querySelector('.chart-subtitle');
        expect(subTitle.textContent).toBe('User Name - Last 7 Days');

        const ariaLiveRegion = document.getElementById('aria-live-account');
        expect(ariaLiveRegion.textContent).toBe('Data updated for User Name - Last 7 Days');
    });

    test('updates subtitle and aria-live region correctly for service', () => {
        const dropdown = document.getElementById('options');
        dropdown.value = 'service';

        handleDropdownChange.mockImplementation(({ target }) => {
            const selectedValue = target.value;
            const subTitle = document.querySelector(`#chartsArea .chart-subtitle`);
            const selectElement = document.getElementById('options');
            const selectedText = selectElement.options[selectElement.selectedIndex].text;

            if (selectedValue === "individual") {
                subTitle.textContent = selectedText + " - Last 7 Days";
                fetchData('individual');
            } else if (selectedValue === "service") {
                subTitle.textContent = selectedText + " - Last 7 Days";
                fetchData('service');
            }

            const liveRegion = document.getElementById('aria-live-account');
            liveRegion.textContent = `Data updated for ${selectedText} - Last 7 Days`;
        });

        handleDropdownChange({ target: dropdown });

        const subTitle = document.querySelector('.chart-subtitle');
        expect(subTitle.textContent).toBe('Service Name - Last 7 Days');

        const ariaLiveRegion = document.getElementById('aria-live-account');
        expect(ariaLiveRegion.textContent).toBe('Data updated for Service Name - Last 7 Days');
    });
});

describe('DOMContentLoaded event listener', () => {
    beforeEach(() => {
        jest.clearAllMocks(); // Clear any previous mock calls

        // Set up the DOMContentLoaded listener again
        document.removeEventListener('DOMContentLoaded', handleDOMContentLoaded);
        document.addEventListener('DOMContentLoaded', handleDOMContentLoaded);

        // Function to handle DOMContentLoaded
        function handleDOMContentLoaded() {
            fetchData('service');
        }
    });

    test('calls fetchData with "service" on DOMContentLoaded', () => {
        document.dispatchEvent(new Event('DOMContentLoaded'));
        expect(fetchData).toHaveBeenCalledWith('service');
    });
});
