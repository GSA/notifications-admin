# BackstopJS Getting Started Guide

## Overview

BackstopJS is currently optional in this project and is used for visual regression testing to ensure consistency in the UI. To get started with BackstopJS, follow the steps below. The official guide can be found at the [BackstopJS GitHub Repository](https://github.com/garris/BackstopJS).

## Goal

Eventually BackstopJS will be implemented in the pipeline process to help catch errors before they make their way to higher environments.

## Prerequisites

Before running BackstopJS, ensure the following:

- Both the API and Admin projects must be running.
- In the .env file of both the API and Admin projects, make sure the following environment variables are uncommented and set to matching values:
  - `NOTIFY_E2E_TEST_EMAIL`
  - `NOTIFY_E2E_TEST_PASSWORD`

Example:

```bash
NOTIFY_E2E_TEST_EMAIL=your-email@example.com
NOTIFY_E2E_TEST_PASSWORD=your-password
```

### How to Run BackstopJS

#### Step 1: Install Gulp Globally

First, make sure all dependencies are installed and updated:

```
make bootstrap
```

#### Step 2: Run the Gulp Test Task

To run the visual regression tests, use the following command:

```
gulp backstopTest
```

If there are new expected changes in the UI, one will need to update the reference images before testing. To do this, run the following command:

```
gulp backstopReference
```

**_Note: After running the `gulp backstopReference` command, immediately running the test (`gulp backstopTest`) should pass all tests, assuming the changes are expected._**

### Adding New Tests

The entry point for BackstopJS configuration can be found in the `backstop.config.js` file.

To add a new feature or page to be tested, modify the `scenarios` array. Refer to the [official documentation](https://github.com/garris/BackstopJS) for details on the structure of the object.

In most cases, one will be testing entire pages instead of individual components. To reduce redundancy, helper functions were created with our default settings that will be applied to every URL in the `urls.js` file. To add a new URL, one would add an object like such:

```
{ label: 'Support', path: '/support' }
```

For unique cases that involve UI interaction, scripts linked to the `engine_scripts/puppeteer` directory can be used to simulate user interactions during tests. An example can be found with `countFeatureLinks.js`
