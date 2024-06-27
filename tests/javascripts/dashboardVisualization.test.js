const { createTable, handleDropdownChange, fetchData, createChart } = require('../../app/assets/javascripts/dashboardVisualization.js');

// Mock d3 to avoid errors related to it
jest.mock('d3', () => {
    const selectAllMock = jest.fn().mockReturnValue({
        remove: jest.fn(),
    });

    const appendMock = jest.fn().mockReturnValue({
        attr: jest.fn().mockReturnThis(),
        append: jest.fn().mockReturnThis(),
        style: jest.fn().mockReturnThis(),
        text: jest.fn(),
    });

    const selectMock = jest.fn().mockReturnValue({
        selectAll: selectAllMock,
        append: appendMock,
        attr: jest.fn().mockReturnThis(),
        style: jest.fn().mockReturnThis(),
        text: jest.fn(),
    });

    const scaleBandMock = jest.fn().mockReturnValue({
        domain: jest.fn().mockReturnThis(),
        range: jest.fn().mockReturnThis(),
        padding: jest.fn().mockReturnThis(),
    });

    const scaleLinearMock = jest.fn().mockReturnValue({
        domain: jest.fn().mockReturnThis(),
        nice: jest.fn().mockReturnThis(),
        range: jest.fn().mockReturnThis(),
    });

    const axisMock = jest.fn().mockReturnThis();

    return {
        select: selectMock,
        scaleBand: scaleBandMock,
        scaleLinear: scaleLinearMock,
        axisBottom: jest.fn(() => axisMock),
        axisLeft: jest.fn(() => axisMock),
        stack: jest.fn(() => jest.fn().mockReturnValue([])),
        format: jest.fn(() => jest.fn()),
    };
});

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
    beforeAll(() => {
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

        createTable('weeklyTable', 'Weekly', labels, deliveredData, failedData);

        const table = document.getElementById('weeklyTable');
        console.log(table);
        expect(document.body.contains(table)).toBe(true);
        expect(table.querySelectorAll('tbody tr').length).toBe(labels.length);
    });
});

describe('Dropdown Change Handler', () => {
    beforeAll(() => {
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

        // Mock Socket.IO
        global.io = jest.fn().mockReturnValue({
            on: jest.fn(),
            emit: jest.fn(),
        });
    });

    test('updates subtitle and aria-live region correctly', () => {
        const dropdown = document.getElementById('options');
        dropdown.value = 'individual';

        handleDropdownChange({ target: dropdown });

        const subTitle = document.querySelector('.chart-subtitle');
        expect(subTitle.textContent).toBe('User Name - Last 7 Days');

        const ariaLiveRegion = document.getElementById('aria-live-account');
        expect(ariaLiveRegion.textContent).toBe('Data updated for User Name - Last 7 Days');
    });
});
