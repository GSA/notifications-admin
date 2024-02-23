# Working with End-to-End Tests

End-to-End (E2E) tests are an important part of a assessing the overall
integrity and stability of a system.  They are a part of the overall
test suite and serve the function of simulating a user working through
the application.  By having comprehensive E2E tests in place, we can
instill higher confidence that future changes and refactorings won't
negatively impact any user experience or break existing functionality.

The US Notify project leverages [`pytest`](https://pytest.org/) for its
existing test suite (at least on the Python side of things) and is now
leveraging [Playwright for Python](https://playwright.dev/python/)
along with its `pytest` plugin for the E2E tests.


## Getting Started

To work with the E2E tests in US Notify, you need to make sure you have
all of the necessary components installed.  The quick and easy way to do
this is to use the Makefile as you did for the initial project setup. In
fact, if you've already done this, you are already set to go!  If not,
then run the bootstrap command in your shell:

```sh
make bootstrap
```

This takes care of installing all of your dependencies, including those
now needed for Playwright.

If you run into certificate errors at the `playwright install` step, try
doing this:

1. Run `brew --prefix` to see Homebrew's root directory

1. Create or modify the local `.env` file in the project and add this
   line:

   `NODE_EXTRA_CA_CERTS=/CHANGE-TO-HOMEBREW-INSTALL-PATH/etc/ca-certificates/cert.pem`

   Make sure to change `CHANGE-TO-HOMEBREW-INSTALL-PATH` to the path
   given by `brew --prefix` in the step above.  For example, if `brew --prefix`
   gave `/opt/homebrew` as output, then the line would look like this:

   `NODE_EXTRA_CA_CERTS=/opt/homebrew/etc/ca-certificates/cert.pem`

1. Save the changes to the `.env` file

1. Run `make bootstrap` again


### Manual Installation

If you need to install things separately, you'll still need to make sure
your environment is set up and configured as outlined in the README.

At your shell in the project root folder, run the following commands:

```sh
poetry install pytest-playwright --dev
poetry run playwright install --with-deps
```

This will install Playwright and its `pytest` plugin, then the
additional dependencies that Playwright requires.

See more details on the
[Playwright for Python Installation page](https://playwright.dev/python/docs/intro).


## Local Configuration

In order to run the E2E tests successfully on your local machine, you'll
also need to make sure you have a `.env` file in the root project folder
and that it has at least these environment variables set in it:

```
# E2E Test Configuration - only set for the Admin site.
NOTIFY_E2E_TEST_URI
NOTIFY_E2E_TEST_EMAIL
NOTIFY_E2E_TEST_PASSWORD
NOTIFY_E2E_AUTH_STATE_PATH
```

This file is **not** checked into source control and is configured to be
ignored in the project's `.gitignore` file; please be careful that it is
not committed to the repo and pushed!


## Running E2E Tests Locally

To run the E2E tests on your local machine, type this command in your
shell at the project root directory:

```sh
make e2e-test
```

You should see `pytest` start producing output and the existing E2E
tests run in multiple headless browsers.


## How to Create and Maintain E2E Tests

All of the E2E tests are found in the `tests/end_to_end` folder and are
written as `pytest` scripts using
[Playwright's Python Framework](https://playwright.dev/python/docs/writing-tests).

Inside the `tests/end_to_end` folder you'll see a `conftest.py` file,
which is similar to the one found in the root `tests` folder but is
specific to the E2E tests.

There a few fixtures defined in here, but the three most important at
this time are these:

- `end_to_end_context`:  A Playwright context object needed to interact
  with a browser instance.
- `authenticated_page`:  A Playwright page object that has gone through
  the sign in process the E2E user is authenticated.
- `unauthenticated_page`:  A Playwright page object that has only loaded
  the home page; no authentication done.

In short, if you're starting a test from scratch and testing pages that
do not require authentication, you'll start with the
`unauthenticated_page` fixture and work from there.

Any test that requires you to be authenticated, you'll start with the
`authenticated_page` object as that'll have taken care of getting
everything set for you and logged into the site with the E2E test user.

The `end_to_end_context` fixture is there more for the two page than for
direct use, but there may be instances where it's easier to get data
or manipulate tests in ways that are better done with the context object
instead of working back from the page object.


### Creating a new test file

If you want to create a new test file to help organize tests (a great
idea!), it will be handy to import the Playwright `expect` and set the
base URL/URI for yourself, like this:

```python
from playwright.sync_api import expect

E2E_TEST_URI = os.getenv("NOTIFY_E2E_TEST_URI")
```

By importing Playwright's `expect` object for tests and setting
something like `E2E_TEST_URI` for yourself, it will make writing tests
much easier.


### Using the fixtures

To use the `authenticated_page` or `unauthenticated_page` fixtures, you
start by defining a test function and then passing in the fixture you
need as a positional argument.  This works the same as the other
functions defined to create a test for pytest.

For example, the test for the landing page starts with this:

```python
def test_landing_page(unauthenticated_page):
    page = unauthenticated_page
    ...
```

Note the passing in of the `unauthenticated_page` fixture - there is no
need to import this or anything, just pass it into the function.  pytest
takes care of everything else for you.

The second line that defines a `page` variable is a convenience, since
you'll be referencing the page object a lot.  This is recommended to
help keep tests readable while keeping fixture names descriptive.

If you need to test an authenticate page, such as the accounts page,
use the `authenticated_page` fixture instead, like so:

```python
def test_add_new_service_workflow(authenticated_page):
    page = authenticated_page
    ...
```

Again, it's helpful to assign the fixture to a `page` variable for easy
reference throughout the test.

Lastly, if you need want access to the Playwright context object that is
used behind the page fixtures, you can reference it directly as well:

```python
def test_add_new_service_workflow(authenticated_page, end_to_end_context):
    page = authenticated_page

    # Prepare for adding a new service later in the test.
    current_date_time = datetime.datetime.now()
    new_service_name = "E2E Federal Test Service {now} - {browser_type}".format(
        now=current_date_time.strftime("%m/%d/%Y %H:%M:%S"),
        browser_type=end_to_end_context.browser.browser_type.name,
    )
    ...
```

In this example, I've used the context to get to the browser object
itself to get the name of the browser for test data.


## Maintaining E2E Tests with GitHub

The E2E tests are configured to run as a separate GitHub action as a
part of our other checks found in `.github/workflows/checks.yml`.

The E2E tests are not run as a part of the regular unit test suite; if
you look at the `Makefile` you'll see that the tests are two separate
commands, with the E2E tests configured separately.

This is done for a couple of reasons:

- Keeps unit tests isolated from the E2E tests
- Allows us to configure E2E tests separately

The environment variables are managed as a part of the GitHub
environment and repository settings.


### E2E Environment Variable Management

These are the E2E test environment variables that must be set:

```
NOTIFY_E2E_TEST_URI
NOTIFY_E2E_TEST_EMAIL
NOTIFY_E2E_TEST_PASSWORD
NOTIFY_E2E_AUTH_STATE_PATH
```

These are only set for the Admin site in GitHub, but must be set
for both GitHub Actions and Dependabot for the same reason as
the MFA environment variables.
